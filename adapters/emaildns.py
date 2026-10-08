"""Email-domain mail-security posture (MIT) — DNS TXT records only.

Reports SPF, DMARC and DKIM configuration of the *domain* (useful for authorized
security audits of an organization). DKIM can only be checked for known common
selectors; a missing hit does not prove DKIM is absent.
"""
from __future__ import annotations

import asyncio
import re

from core.schema import Finding, ModuleResult

from .base import Adapter
from .emailcheck import DNS_OK, query_dns

COMMON_DKIM_SELECTORS = ["default", "google", "selector1", "selector2", "k1", "mail", "dkim", "s1", "s2"]
_ALL_RE = re.compile(r"(?:^|\s)([+?~-]?all)(?:\s|$)")
_P_RE = re.compile(r"(?:^|;)\s*p=([a-zA-Z]+)")



def parse_spf(txt: str) -> tuple[str, str]:
    """Return (all-mechanism, verdict) for an SPF record."""
    m = _ALL_RE.search(txt)
    mech = m.group(1) if m else "none"
    verdict = {
        "-all": "strict (hard fail)", "~all": "soft fail",
        "?all": "neutral (weak)", "+all": "open (anyone may send — insecure)",
        "all": "open (anyone may send — insecure)",
    }.get(mech, "no all-mechanism (weak)")
    return mech, verdict


def parse_dmarc(txt: str) -> str:
    m = _P_RE.search(txt)
    return m.group(1).lower() if m else "unknown"


def _txt(domain: str) -> list[str]:
    """TXT records of a name, flattened to strings (empty if none)."""
    try:
        answers = query_dns(domain, "TXT")
    except Exception:  # NXDOMAIN, timeouts, no dnspython …: treat as "no record"
        return []
    return [b"".join(r.strings).decode(errors="replace") for r in answers]


class EmailDNSAdapter(Adapter):
    name = "emaildns"
    inputs = {"email"}
    timeout_s = 40

    async def health(self) -> dict:
        if not DNS_OK:
            return {"available": False, "detail": "not installed — pip install dnspython"}
        return {"available": True, "detail": "SPF / DMARC / common DKIM selectors (DNS TXT)"}

    async def run(self, target, ctx) -> ModuleResult:
        if not DNS_OK:
            return ModuleResult(module=self.name, status="unavailable",
                                warnings=["dnspython not installed"])
        domain = target.email.rsplit("@", 1)[1]
        loop = asyncio.get_running_loop()
        findings: list[Finding] = []
        warnings: list[str] = []

        async def txt(name):
            return await loop.run_in_executor(None, _txt, name)

        # all lookups run concurrently so a slow resolver cannot exceed the module timeout
        spf_txt, dmarc_txt, *dkim_txt = await asyncio.gather(
            txt(domain), txt(f"_dmarc.{domain}"),
            *(txt(f"{sel}._domainkey.{domain}") for sel in COMMON_DKIM_SELECTORS),
        )
        spf = [t for t in spf_txt if t.lower().startswith("v=spf1")]
        if spf:
            mech, verdict = parse_spf(spf[0])
            findings.append(Finding(type="validity", key="SPF", value=f"{verdict} ({mech})",
                                    confidence="high", source=self.name))
            if mech == "+all":
                warnings.append("SPF ends in +all: any server may send mail as this domain")
        else:
            findings.append(Finding(type="validity", key="SPF", value="no SPF record",
                                    confidence="high", source=self.name))

        dmarc = [t for t in dmarc_txt if t.lower().startswith("v=dmarc1")]
        if dmarc:
            policy = parse_dmarc(dmarc[0])
            findings.append(Finding(type="validity", key="DMARC policy", value=policy,
                                    confidence="high", source=self.name))
            if policy == "none":
                warnings.append("DMARC p=none: spoofed mail is monitored, not blocked")
        else:
            findings.append(Finding(type="validity", key="DMARC policy", value="no DMARC record",
                                    confidence="high", source=self.name))

        hits = [sel for sel, recs in zip(COMMON_DKIM_SELECTORS, dkim_txt)
                if any("p=" in t for t in recs)]
        if hits:
            findings.append(Finding(type="validity", key="DKIM selectors found",
                                    value=", ".join(hits), confidence="high", source=self.name))
        else:
            findings.append(Finding(type="validity", key="DKIM selectors found",
                                    value="none of the common selectors",
                                    confidence="low", source=self.name))
            warnings.append("DKIM: no common selector matched (custom selectors are not enumerated)")
        return ModuleResult(module=self.name, status="ok", findings=findings, warnings=warnings)
