"""email2phonenumber adapter — vendored MIT script, subprocess, experimental.

Author's own README: original services added captchas/protections → PoC status.
We run `scrape` mode only; `bruteforce` is never invoked by TelScope.
"""
from __future__ import annotations

import re
import sys

from core.schema import Finding, ModuleResult

from .base import Adapter, REPO_ROOT, run_cmd

SCRIPT = REPO_ROOT / "vendor" / "email2phonenumber" / "email2phonenumber.py"
DIGIT_HINT = re.compile(r"(?:last|ends? with|digits?(?: found)?)\D{0,12}(\d{2,4})", re.I)
MASKED = re.compile(r"\+\d[\d\s\-().]{4,16}\d")


class Email2PhoneAdapter(Adapter):
    name = "email2phone"
    inputs = {"email"}
    timeout_s = 180

    async def health(self) -> dict:
        if not SCRIPT.exists():
            return {"available": False,
                    "detail": "vendor missing — run bootstrap.py (clones email2phonenumber)"}
        return {"available": True,
                "detail": "martinvigo/email2phonenumber · scrape mode (experimental)"}

    async def run(self, target, ctx) -> ModuleResult:
        if not SCRIPT.exists():
            return ModuleResult(module=self.name, status="unavailable",
                                warnings=["vendor/email2phonenumber missing"])
        rc, out = await run_cmd(
            [sys.executable, str(SCRIPT), "scrape", "-e", target.email],
            self.timeout_s,
        )
        text = out.decode(errors="replace")
        findings: list[Finding] = []
        warnings: list[str] = []
        for m in re.finditer(r"Scraping ([A-Za-z0-9.\-]+)", text):
            ctx.log(f"email2phone: scraping {m.group(1)}")
        for m in DIGIT_HINT.finditer(text):
            findings.append(Finding(type="raw", key="digit_fragment",
                                    value=m.group(1), confidence="low",
                                    source="email2phone"))
        for m in MASKED.finditer(text):
            findings.append(Finding(type="raw", key="masked_number",
                                    value=m.group(0).strip(), confidence="low",
                                    source="email2phone"))
        if "Traceback" in text:
            warnings.append("some services unreachable/blocked (PoC tool — experimental)")
        status = "ok" if (findings or "Scraping" in text) else "error"
        return ModuleResult(module=self.name, status=status, findings=findings[:40],
                            warnings=warnings, raw_log=text[:20000])
