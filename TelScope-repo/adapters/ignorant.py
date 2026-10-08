"""Ignorant adapter — CLI subprocess (GPL-3.0 stays out of our process).

Verified output grammar (v1.2, 2026-10-08), with --no-color --no-clear:
  [+] domain  -> account exists · [-] domain -> not used · [x] domain -> rate limit
"""
from __future__ import annotations

import re

from core.schema import Finding, ModuleResult

from .base import Adapter, run_cmd, strip_ansi, which_tool

LINE_RE = re.compile(r"^\s*\[([+\-x])\]\s+([A-Za-z0-9.\-]+)\s*$")


class IgnorantAdapter(Adapter):
    name = "ignorant"
    inputs = {"phone"}
    timeout_s = 90

    async def health(self) -> dict:
        p = which_tool(["ignorant"])
        if not p:
            return {"available": False, "detail": "not installed — pip install ignorant"}
        return {"available": True, "detail": "ignorant CLI (pip, v1.2)"}

    async def run(self, target, ctx) -> ModuleResult:
        p = which_tool(["ignorant"])
        if not p:
            return ModuleResult(module=self.name, status="unavailable",
                                warnings=["ignorant not installed"])
        rc, out = await run_cmd(
            [p, str(target.country_code), str(target.national),
             "--no-color", "--no-clear", "-T", "10"],
            self.timeout_s,
        )
        text = strip_ansi(out.decode(errors="replace"))
        for line in text.splitlines():
            if line.strip():
                ctx.log(f"ignorant: {line.strip()}")
        findings: list[Finding] = []
        warnings: list[str] = []
        for line in text.splitlines():
            m = LINE_RE.match(line)
            if not m:
                continue
            flag, domain = m.groups()
            if flag == "+":
                value, conf = "registered", "high"
            elif flag == "-":
                value, conf = "not registered", "high"
            else:
                value, conf = "rate-limited", "low"
                warnings.append(f"{domain}: rate-limited — change IP / slow down")
            findings.append(Finding(type="platform", key=domain, value=value,
                                    confidence=conf, source="ignorant"))
        status = "ok" if findings else ("error" if "Traceback" in text or rc != 0 else "ok")
        if not findings and not warnings:
            warnings.append("no platform lines parsed — see raw log")
        return ModuleResult(module=self.name, status=status, findings=findings,
                            warnings=warnings, raw_log=text[:20000])
