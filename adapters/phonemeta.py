"""Phone metadata adapter (MIT) — fully LOCAL, no network calls.

Uses Google's libphonenumber port (`phonenumbers`, Apache-2.0) to report what the
number format itself reveals: validity, line type, prefix-based carrier and
region/timezones. Carrier data is prefix-based and can be stale because of
number portability, so it is reported with medium confidence.
"""
from __future__ import annotations

from core.schema import Finding, ModuleResult

from .base import Adapter

_TYPE_NAMES = {
    "FIXED_LINE": "fixed line", "MOBILE": "mobile", "FIXED_LINE_OR_MOBILE": "fixed line or mobile",
    "TOLL_FREE": "toll free", "PREMIUM_RATE": "premium rate", "SHARED_COST": "shared cost",
    "VOIP": "VoIP", "PERSONAL_NUMBER": "personal number", "PAGER": "pager",
    "UAN": "UAN", "VOICEMAIL": "voicemail", "UNKNOWN": "unknown",
}


class PhoneMetaAdapter(Adapter):
    name = "phonemeta"
    inputs = {"phone"}
    timeout_s = 20

    async def health(self) -> dict:
        try:
            import phonenumbers  # noqa: F401
        except ImportError:
            return {"available": False, "detail": "not installed — pip install phonenumbers"}
        return {"available": True, "detail": "libphonenumber metadata (offline)"}

    async def run(self, target, ctx) -> ModuleResult:
        import phonenumbers
        from phonenumbers import carrier, geocoder, number_type, timezone

        parsed = phonenumbers.parse(target.e164, None)
        findings: list[Finding] = []
        valid = phonenumbers.is_valid_number(parsed)
        possible = phonenumbers.is_possible_number(parsed)
        findings.append(Finding(
            type="validity", key="number validity",
            value="valid" if valid else ("possible (not confirmed)" if possible else "invalid"),
            confidence="high", source=self.name))

        t = number_type(parsed)
        tname = _TYPE_NAMES.get(_type_key(t), "unknown")
        findings.append(Finding(type="line_type", key="line type", value=tname,
                                confidence="high" if valid else "medium", source=self.name))

        region = geocoder.description_for_number(parsed, "en")
        if region:
            findings.append(Finding(type="region", key="region", value=region,
                                    confidence="medium", source=self.name))
        zones = timezone.time_zones_for_number(parsed)
        if zones:
            findings.append(Finding(type="region", key="timezones", value=", ".join(zones),
                                    confidence="medium", source=self.name))
        car = carrier.name_for_number(parsed, "en")
        if car:
            findings.append(Finding(type="carrier", key="carrier (prefix-based)", value=car,
                                    confidence="medium", source=self.name))

        warnings = []
        if not car:
            warnings.append("no carrier data for this number prefix")
        return ModuleResult(module=self.name, status="ok", findings=findings, warnings=warnings)


def _type_key(t) -> str:
    """Map a libphonenumber PhoneNumberType int to its enum name."""
    import phonenumbers
    for name in _TYPE_NAMES:
        if getattr(phonenumbers.PhoneNumberType, name, None) == t:
            return name
    return "UNKNOWN"
