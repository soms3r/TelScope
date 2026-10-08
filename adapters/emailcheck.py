"""Email domain checks (MIT) — DNS + static list only. NO mailbox probing.

Checks the domain's MX/A records and whether the domain is a known disposable-mail
provider. It never connects to a mail server, sends mail, or tries to confirm a
mailbox exists.
"""
from __future__ import annotations

import asyncio

from core.schema import Finding, ModuleResult

try:  # never let a missing optional package break app startup
    import dns.exception
    import dns.resolver
    DNS_OK = True
except ImportError:  # pragma: no cover
    DNS_OK = False

from .base import Adapter

# Small illustrative list of disposable-mail domains. Extend as needed.
DISPOSABLE = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com",
    "yopmail.com", "trashmail.com", "throwawaymail.com", "sharklasers.com",
}


def query_dns(domain: str, rtype: str):
    """Single DNS query (module-level so tests can replace it)."""
    r = dns.resolver.Resolver()
    r.lifetime = 8
    return r.resolve(domain, rtype)


def classify_domain(mx_hosts: list[str] | None, has_a: bool | None, nxdomain: bool = False) -> str:
    """Pure helper: turn DNS answers into a human-readable domain state."""
    if nxdomain:
        return "domain does not exist"
    if mx_hosts:
        return "accepts mail (MX present)"
    if has_a:
        return "no MX; A record only (may not receive mail)"
    return "no MX or A record"


class EmailCheckAdapter(Adapter):
    name = "emailcheck"
    inputs = {"email"}
    timeout_s = 25

    async def health(self) -> dict:
        if not DNS_OK:
            return {"available": False, "detail": "not installed — pip install dnspython"}
        return {"available": True, "detail": "DNS MX/A + disposable list (no mailbox probing)"}

    async def run(self, target, ctx) -> ModuleResult:
        if not DNS_OK:
            return ModuleResult(module=self.name, status="unavailable",
                                warnings=["dnspython not installed"])
        domain = target.email.rsplit("@", 1)[1]
        loop = asyncio.get_running_loop()
        findings: list[Finding] = []
        warnings: list[str] = []
        mx_hosts, has_a, nx = None, None, False
        try:
            mx = await loop.run_in_executor(None, query_dns, domain, "MX")
            mx_hosts = sorted(str(x.exchange).rstrip(".") for x in mx)
            findings.append(Finding(type="validity", key="mail servers (MX)",
                                    value=", ".join(mx_hosts[:5]), confidence="high",
                                    source=self.name))
        except dns.resolver.NXDOMAIN:
            nx = True
        except dns.resolver.NoAnswer:
            try:
                await loop.run_in_executor(None, query_dns, domain, "A")
                has_a = True
            except dns.exception.DNSException:
                has_a = False
        except dns.exception.DNSException as exc:
            warnings.append(f"DNS error: {type(exc).__name__}")

        state = classify_domain(mx_hosts, has_a, nx) if not warnings else "DNS lookup failed"
        findings.append(Finding(type="validity", key="domain", value=state,
                                confidence="high" if mx_hosts or nx else "medium",
                                source=self.name))
        disposable = domain in DISPOSABLE
        findings.append(Finding(type="validity", key="disposable provider",
                                value="yes (known disposable domain)" if disposable else "no match in list",
                                confidence="medium", source=self.name))
        return ModuleResult(module=self.name, status="ok", findings=findings, warnings=warnings)
