"""Target normalization: any-country phone -> E.164, or email (MIT)."""
from __future__ import annotations

import re

from .schema import Target

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
E164_FALLBACK = re.compile(r"^\+([1-9]\d{0,3})(\d{4,14})$")


def parse_target(raw: str, default_region: str = "BD") -> Target:
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Empty target")
    if EMAIL_RE.match(raw):
        return Target(type="email", raw=raw, email=raw.lower())
    try:  # preferred: Google libphonenumber port
        import phonenumbers

        parsed = phonenumbers.parse(raw, default_region or None)
        if not (
            phonenumbers.is_valid_number(parsed)
            or phonenumbers.is_possible_number(parsed)
        ):
            raise ValueError("Invalid or impossible phone number")
        e164 = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        )
        return Target(
            type="phone",
            raw=raw,
            e164=e164,
            country_code=parsed.country_code,
            national=str(parsed.national_number),
            region=phonenumbers.region_code_for_number(parsed) or default_region,
        )
    except ImportError:  # degraded mode: raw E.164 only
        m = E164_FALLBACK.match(raw)
        if not m:
            raise ValueError(
                "Invalid phone number (install 'phonenumbers' for full validation)"
            )
        return Target(
            type="phone", raw=raw, e164=raw,
            country_code=int(m.group(1)), national=m.group(2),
        )
    except ValueError:
        raise
    except Exception as exc:  # phonenumbers errors
        raise ValueError(f"Invalid phone number: {exc}") from exc
