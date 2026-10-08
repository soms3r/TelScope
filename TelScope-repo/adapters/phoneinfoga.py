"""PhoneInfoga adapter — talks to its OWN REST API (separate process, GPL-safe).

Verified against v2.11.0 (2026-10-08):
  GET  /api/                                  -> version info
  GET  /api/v2/scanners                       -> scanner list
  POST /api/v2/scanners/{name}/run            -> body {"number": "<digits, no +>"}
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Optional

import httpx

from core.schema import Finding, ModuleResult

from .base import Adapter, REPO_ROOT, run_cmd, which_tool

_server: Optional[tuple] = None  # (proc_or_None, base_url)


class PhoneInfogaAdapter(Adapter):
    name = "phoneinfoga"
    inputs = {"phone"}
    timeout_s = 120

    def binary(self) -> Optional[str]:
        exe = "phoneinfoga.exe" if os.name == "nt" else "phoneinfoga"
        local = REPO_ROOT / "bin" / exe
        if local.exists():
            return str(local)
        return which_tool(["phoneinfoga"])

    async def health(self) -> dict:
        b = self.binary()
        if not b:
            return {
                "available": False,
                "detail": "binary missing — run bootstrap.py or drop it in bin/",
            }
        try:
            _, out = await run_cmd([b, "version"], 10)
            ver = out.decode(errors="replace").strip()
        except Exception as exc:
            ver = f"present (version probe failed: {exc})"
        return {"available": True, "detail": ver}

    async def _ensure_server(self, port: int, log) -> str:
        global _server
        base = f"http://127.0.0.1:{port}"

        async def alive() -> bool:
            try:
                async with httpx.AsyncClient(timeout=3) as c:
                    return (await c.get(base + "/api/")).status_code == 200
            except Exception:
                return False

        if await alive():
            _server = (_server[0] if _server else None, base)
            return base
        b = self.binary()
        if not b:
            raise RuntimeError("phoneinfoga binary missing")
        proc = await asyncio.create_subprocess_exec(
            b, "serve", "--no-client", "-p", str(port),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(24):
            await asyncio.sleep(0.5)
            if await alive():
                break
        else:
            proc.kill()
            raise RuntimeError("phoneinfoga REST server did not become ready")
        _server = (proc, base)
        log(f"phoneinfoga REST server up on :{port}")
        return base

    async def run(self, target, ctx) -> ModuleResult:
        port = int(ctx.settings.get("phoneinfoga_port", "5001"))
        base = await self._ensure_server(port, ctx.log)
        digits = (target.e164 or "").lstrip("+")
        scanners = ["local", "ovh", "googlesearch"]
        if ctx.settings.get("numverify_key", "").strip():
            scanners.insert(1, "numverify")

        findings: list[Finding] = []
        warnings: list[str] = []
        raw: dict = {}
        async with httpx.AsyncClient(timeout=25) as c:
            for s in scanners:
                try:
                    r = await c.post(
                        f"{base}/api/v2/scanners/{s}/run", json={"number": digits}
                    )
                    data = r.json()
                except Exception as exc:
                    warnings.append(f"{s}: {exc}")
                    continue
                if isinstance(data, dict) and data.get("error"):
                    warnings.append(f"{s}: {data['error']}")
                    continue
                res = (data or {}).get("result") or {}
                raw[s] = res
                ctx.log(f"phoneinfoga/{s}: ok")
                if s == "local":
                    if res.get("e164"):
                        findings.append(Finding(
                            type="region", key="e164", value=res["e164"],
                            confidence="high", source="phoneinfoga"))
                    if res.get("country_code"):
                        findings.append(Finding(
                            type="region", key="country_code",
                            value=f"+{res['country_code']}",
                            confidence="high", source="phoneinfoga"))
                elif s == "numverify":
                    if res.get("carrier"):
                        findings.append(Finding(
                            type="carrier", key="carrier", value=str(res["carrier"]),
                            confidence="high", source="phoneinfoga/numverify"))
                    if res.get("line_type"):
                        findings.append(Finding(
                            type="line_type", key="line_type",
                            value=str(res["line_type"]),
                            confidence="high", source="phoneinfoga/numverify"))
                    if res.get("country_name"):
                        findings.append(Finding(
                            type="region", key="country",
                            value=str(res["country_name"]),
                            confidence="high", source="phoneinfoga/numverify"))
                elif s == "ovh":
                    if res and (res.get("valid") or res.get("found")):
                        findings.append(Finding(
                            type="carrier", key="voip",
                            value="OVH Telecom (VoIP range)",
                            confidence="medium", source="phoneinfoga/ovh"))
                elif s == "googlesearch":
                    for item in (res.get("social_media") or [])[:8]:
                        url = item.get("url")
                        dork = item.get("dork", "")
                        if url:
                            site = dork.split(" ")[0].replace("site:", "") if dork else "web"
                            findings.append(Finding(
                                type="link", key=f"dork:{site}", value=url,
                                confidence="low",
                                source="phoneinfoga/googlesearch"))
        status = "ok" if findings else ("error" if warnings else "ok")
        return ModuleResult(
            module=self.name, status=status, findings=findings,
            warnings=warnings, raw_log=json.dumps(raw, indent=1)[:20000],
        )

    async def shutdown(self) -> None:
        global _server
        if _server and _server[0] is not None:
            try:
                _server[0].kill()
            except Exception:
                pass
        _server = None
