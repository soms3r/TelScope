"""Have I Been Pwned (HIBP) v3 adapters (MIT) — breach & paste exposure for an email you own
or are authorized to check.

Both modules use the official HIBP v3 API and need a subscription or test key in
settings (`hibp_api_key`, 32 hex chars). The key goes only in the `hibp-api-key`
header; the user-agent identifies the app as HIBP's terms require.

Only metadata is read: breach names/dates/data classes and paste titles/dates/counts.
Paste bodies and breached credentials are never requested or stored.
"""
from __future__ import annotations

import re
from urllib.parse import quote

import httpx

from core.schema import Finding, ModuleResult

from .base import Adapter, current_settings

BASE = "https://haveibeenpwned.com/api/v3/"
KEY_RE = re.compile(r"^[0-9a-fA-F]{32}$")
UA = "TelScope/2.0 (local OSINT dashboard; authorized use)"


def api_key() -> str:
    return (current_settings().get("hibp_api_key") or "").strip()


class _HIBPBase(Adapter):
    endpoint = ""          # e.g. "breachedaccount/{}"
    params: dict = {}
    not_found_note = ""    # HIBP answers 404 when the address has no records

    async def health(self) -> dict:
        key = api_key()
        if not key:
            return {"available": False,
                    "detail": "set hibp_api_key in settings (HIBP subscription or test key)"}
        if not KEY_RE.match(key):
            return {"available": False, "detail": "hibp_api_key must be 32 hex characters"}
        return {"available": True, "detail": f"HIBP v3 {self.endpoint.split('/')[0]} (keyed)"}

    def parse(self, data) -> list[Finding]:  # pragma: no cover - overridden
        raise NotImplementedError

    async def run(self, target, ctx) -> ModuleResult:
        key = api_key()
        if not KEY_RE.match(key):
            return ModuleResult(module=self.name, status="unavailable",
                                warnings=["no valid HIBP API key in settings"])
        url = BASE + self.endpoint.format(quote(target.email, safe=""))
        async with httpx.AsyncClient(
            timeout=20, headers={"hibp-api-key": key, "user-agent": UA}
        ) as client:
            r = await client.get(url, params=self.params)
        ctx.log(f"{self.name}: HTTP {r.status_code}")

        if r.status_code == 404:
            return ModuleResult(module=self.name, status="ok", findings=[],
                                warnings=[self.not_found_note])
        if r.status_code == 401:
            return ModuleResult(module=self.name, status="error",
                                warnings=["HIBP rejected the API key"])
        if r.status_code == 429:
            wait = r.headers.get("retry-after", "?")
            return ModuleResult(module=self.name, status="error",
                                warnings=[f"HIBP rate limit — retry after {wait}s"])
        if r.status_code != 200:
            return ModuleResult(module=self.name, status="error",
                                warnings=[f"HIBP returned HTTP {r.status_code}"])
        return ModuleResult(module=self.name, status="ok", findings=self.parse(r.json()))


class HIBPAdapter(_HIBPBase):
    """Breaches the address appears in (metadata: date, data classes)."""
    name = "hibp"
    inputs = {"email"}
    timeout_s = 40
    endpoint = "breachedaccount/{}"
    params = {"truncateResponse": "false"}
    not_found_note = "no known breaches for this address"

    def parse(self, data) -> list[Finding]:
        out = []
        for b in data:
            classes = ", ".join(b.get("DataClasses", [])) or "unspecified"
            out.append(Finding(
                type="breach", key=b.get("Title") or b.get("Name", "?"),
                value=f"breached {b.get('BreachDate', '?')} · data: {classes}",
                confidence="high", source=self.name))
        return out


class HIBPPastesAdapter(_HIBPBase):
    """Pastes that list the address (metadata only: source, date, count)."""
    name = "hibp_pastes"
    inputs = {"email"}
    timeout_s = 40
    endpoint = "pasteaccount/{}"
    not_found_note = "no pastes found for this address"

    def parse(self, data) -> list[Finding]:
        out = []
        for p in data:
            out.append(Finding(
                type="breach", key=f"paste · {p.get('Source', '?')}",
                value=f"{p.get('Date', '?')} · {p.get('EmailCount', '?')} addresses in paste"
                      + (f" · “{p['Title']}”" if p.get("Title") else ""),
                confidence="high", source=self.name))
        return out
