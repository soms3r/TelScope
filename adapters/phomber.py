"""Phomber adapter — REPL driven through a pseudo-terminal (GPL-safe, separate process).

Verified (3.1.1, 2026-10-08): `phomber -s` under a pty accepts piped commands;
`number +E164` prints an INFORMATION/DESCRIPTION table.
"""
from __future__ import annotations

import os
import re

from core.schema import Finding, ModuleResult

from .base import Adapter, run_pty, strip_ansi, which_tool

ROW_RE = re.compile(r"\|\s*([A-Za-z][A-Za-z /()-]*?)\s*\|\s*([^|]*?)\s*\|")


class PhomberAdapter(Adapter):
    name = "phomber"
    inputs = {"phone"}
    timeout_s = 150

    async def health(self) -> dict:
        if os.name != "posix":
            return {"available": False,
                    "detail": "phomber REPL needs a POSIX pty — unavailable on Windows"}
        p = which_tool(["phomber"])
        if not p:
            return {"available": False, "detail": "not installed — pip install phomber"}
        return {"available": True, "detail": "phomber CLI (pip, v3.1.1, pty-driven)"}

    async def run(self, target, ctx) -> ModuleResult:
        p = which_tool(["phomber"])
        if not p or os.name != "posix":
            return ModuleResult(module=self.name, status="unavailable",
                                warnings=["phomber unavailable on this platform"])
        rc, out = await run_pty(
            [p, "-s"], f"number {target.e164}\nexit\n", self.timeout_s
        )
        text = strip_ansi(out.decode(errors="replace"))
        ctx.log("phomber: pty session complete")
        findings: list[Finding] = []
        for m in ROW_RE.finditer(text):
            k, v = m.group(1).strip(), m.group(2).strip()
            if not v or k.upper() in ("INFORMATION", "DESCRIPTION") or set(k) <= set("-─"):
                continue
            kl = k.lower()
            if "carrier" in kl or "operator" in kl:
                ftype = "carrier"
            elif "line" in kl and "type" in kl:
                ftype = "line_type"
            elif any(x in kl for x in ("region", "location", "geocoder", "country", "timezone", "time zone")):
                ftype = "region"
            elif "valid" in kl or "possible" in kl:
                ftype = "validity"
            else:
                ftype = "raw"
            findings.append(Finding(type=ftype, key=k, value=v,
                                    confidence="medium", source="phomber"))
        status = "ok" if findings else ("error" if "Traceback" in text else "ok")
        if not findings:
            findings_note = "no table rows parsed — see raw log"
        else:
            findings_note = ""
        warnings = [findings_note] if findings_note else []
        return ModuleResult(module=self.name, status=status, findings=findings,
                            warnings=warnings, raw_log=text[:20000])
