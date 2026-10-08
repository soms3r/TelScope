"""Moriarty / Gökbörü Intelligence adapter — vendor CLI subprocess (MIT tool).

Verified (repo @ 571a78f, 2026-10-08): CLI-USAGE.md documents
  bash ./moriarty-local phone-audit "+E164" --i-own-this-number \
       --sources local,reputation --timeout N --output out.json
NOTE: the PyPI package `moriarty-project` is a DIFFERENT tool (IOC kit) — not used.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from core.schema import Finding, ModuleResult

from .base import Adapter, REPO_ROOT, run_cmd

VENDOR = REPO_ROOT / "vendor" / "Gokboru_Intel"


def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


class MoriartyAdapter(Adapter):
    name = "moriarty"
    inputs = {"phone"}
    timeout_s = 200

    @staticmethod
    def venv_python() -> Path:
        base = Path(os.environ.get(
            "XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
        return base / "moriarty-v5" / "venv" / "bin" / "python"

    async def health(self) -> dict:
        if not (VENDOR / "moriarty-local").exists():
            return {"available": False,
                    "detail": "vendor missing — run bootstrap.py (clones Gökbörü Intel)"}
        if not self.venv_python().exists():
            return {"available": False,
                    "detail": "one-time setup pending: bash vendor/Gokboru_Intel/install.sh"}
        return {"available": True,
                "detail": "Gökbörü Intelligence (AzizKpln) · moriarty-local CLI"}

    async def run(self, target, ctx) -> ModuleResult:
        if not (VENDOR / "moriarty-local").exists():
            return ModuleResult(module=self.name, status="unavailable",
                                warnings=["vendor/Gokboru_Intel missing"])
        if not self.venv_python().exists():
            return ModuleResult(
                module=self.name, status="unavailable",
                warnings=["Gökbörü venv missing — run once on this machine: "
                          "bash vendor/Gokboru_Intel/install.sh (GUI installer)"])
        fd, out_json = tempfile.mkstemp(suffix=".json", prefix="telscope-moriarty-")
        os.close(fd)
        argv = ["bash", "moriarty-local", "phone-audit", target.e164,
                "--i-own-this-number", "--sources", "local,reputation",
                "--timeout", "90", "--output", out_json]
        if shutil.which("xvfb-run"):
            argv = ["xvfb-run", "-a"] + argv
        try:
            rc, out = await run_cmd(argv, self.timeout_s, cwd=VENDOR)
        finally:
            pass
        text = out.decode(errors="replace")
        ctx.log("moriarty: phone-audit finished")
        findings: list[Finding] = []
        warnings: list[str] = []
        data = None
        try:
            data = json.loads(Path(out_json).read_text() or "null")
        except Exception:
            data = None
        if data is not None:
            for d in _walk(data):
                src = d.get("source") or d.get("site") or d.get("name")
                state = d.get("status") or d.get("found") or d.get("exists") or d.get("result")
                if src and state is not None and isinstance(src, str):
                    findings.append(Finding(type="platform", key=src,
                                            value=str(state), confidence="medium",
                                            source="moriarty"))
                for lk in ("url", "link", "report"):
                    if isinstance(d.get(lk), str) and d[lk].startswith("http"):
                        findings.append(Finding(type="link", key=src or lk,
                                                value=d[lk], confidence="low",
                                                source="moriarty"))
        if not findings:
            for line in text.splitlines():
                if "http://" in line or "https://" in line:
                    url = line.split()[-1]
                    findings.append(Finding(type="link", key="report", value=url,
                                            confidence="low", source="moriarty"))
        if not findings:
            warnings.append("no structured findings — see raw log (sources may need xvfb/API keys)")
        return ModuleResult(module=self.name,
                            status="ok" if findings or data is not None else "error",
                            findings=findings[:60], warnings=warnings,
                            raw_log=(text + "\n---\n" + (Path(out_json).read_text(errors="replace") if Path(out_json).exists() else ""))[:20000])
