"""Domain registration via RDAP (MIT) — public registry data about the email's DOMAIN.

Uses the RDAP redirector (rdap.org), which forwards to the authoritative registry.
Only operational facts are read: registrar name, registration/expiry dates,
status flags and nameservers.

Deliberately NOT read: registrant / admin / tech contact entities and any
personal fields (name, email, phone, postal address). Free-mail providers
(gmail.com, outlook.com, …) are skipped: their registration belongs to the
provider, not to the person using the address.
"""
from __future__ import annotations

import httpx

from core.schema import Finding, ModuleResult

from .base import Adapter

RDAP = "https://rdap.org/domain/{}"
UA = "TelScope/2.0 (local OSINT dashboard; authorized use)"
FREE_MAIL = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com", "msn.com",
    "yahoo.com", "icloud.com", "me.com", "aol.com", "proton.me", "protonmail.com",
    "gmx.com", "gmx.net", "yandex.com", "mail.ru", "qq.com", "163.com", "zoho.com",
    "hey.com", "duck.com",
}


def _fn_from_vcard(vcard) -> str:
    try:
        for entry in vcard[1]:
            if entry[0] == "fn":
                return str(entry[3])
    except (IndexError, TypeError):
        pass
    return ""


def parse_rdap(doc: dict) -> list[Finding]:
    """Pure helper: RDAP JSON -> operational findings (no contact data)."""
    out: list[Finding] = []

    def add(key, value, conf="high"):
        out.append(Finding(type="validity", key=key, value=value, confidence=conf, source="domainrdap"))

    for ev in doc.get("events", []):
        action, date = ev.get("eventAction", ""), ev.get("eventDate", "")
        if action == "registration":
            add("registered", date[:10])
        elif action == "expiration":
            add("expires", date[:10])
    for ent in doc.get("entities", []):
        if "registrar" in ent.get("roles", []):   # registrar only; never registrant/admin/tech
            name = _fn_from_vcard(ent.get("vcardArray", []))
            if name:
                add("registrar", name)
    ns = [n.get("ldhName", "").lower() for n in doc.get("nameservers", []) if n.get("ldhName")]
    if ns:
        add("nameservers", ", ".join(ns[:4]))
    statuses = [s.replace(" ", "") for s in doc.get("status", [])]
    if statuses:
        add("status", ", ".join(statuses[:4]), "medium")
    return out


class DomainRDAPAdapter(Adapter):
    name = "domainrdap"
    inputs = {"email"}
    timeout_s = 30

    async def health(self) -> dict:
        return {"available": True, "detail": "RDAP via rdap.org (public registry data)"}

    async def run(self, target, ctx) -> ModuleResult:
        domain = target.email.rsplit("@", 1)[1]
        if domain in FREE_MAIL:
            return ModuleResult(module=self.name, status="ok", findings=[],
                                warnings=["free-mail provider: registration belongs to the provider, skipped"])
        async with httpx.AsyncClient(timeout=20, follow_redirects=True,
                                     headers={"accept": "application/rdap+json",
                                              "user-agent": UA}) as client:
            r = await client.get(RDAP.format(domain))
        ctx.log(f"domainrdap: HTTP {r.status_code}")
        if r.status_code == 404:
            return ModuleResult(module=self.name, status="ok", findings=[],
                                warnings=["no RDAP record for this domain (ccTLD may lack RDAP)"])
        if r.status_code == 429:
            return ModuleResult(module=self.name, status="error",
                                warnings=["RDAP rate limit — try again later"])
        if r.status_code != 200:
            return ModuleResult(module=self.name, status="error",
                                warnings=[f"RDAP returned HTTP {r.status_code}"])
        return ModuleResult(module=self.name, status="ok", findings=parse_rdap(r.json()))
