# Version pins (recorded 2026-10-08, see INTEGRATION-NOTES.md)

| Component | Pin | Verification |
|---|---|---|
| PhoneInfoga | `v2.11.0` (asset per platform) | `sha256sum -c phoneinfoga_checksums.txt` at bootstrap; Linux_x86_64 tar.gz sha256 `6173dfc4ec009a6fe688068bac5a250646f5a8f56409098f5edcc7e404b12a52` |
| ignorant (pip) | `>=1.2` | CLI grammar verified |
| phomber (pip) | `>=3.1.1` | pty driver verified |
| email2phonenumber | commit `9df9dbe838d4e32208b358df6de299474ff22a7d` | vendored by bootstrap |
| X-osint | commit `3c68bd8cecda4bc7865ea0dfbd6d55458aabaffe` | vendored by bootstrap |
| Gokboru_Intel (Moriarty) | commit `571a78fb59ca4b437e0daedebe90d4926e428ba9` | vendored by bootstrap |

**Not used:** PyPI `moriarty-project` — different tool (IOC kit), broken vs selectolax ≥1.0.
Bootstrap re-verifies checksums at download time; pins are bumped only with updated notes.

## Added 2026-10-08 (modules v1.1)

| Component | Pin | Notes |
|---|---|---|
| dnspython (pip) | `>=2.6` (ISC) | MX/A lookups for `emailcheck` only; no mailbox probing |
| phonenumbers (pip) | `>=8.13` (Apache-2.0) | Already a core dep; now also drives `phonemeta` (offline) |
| HIBP API v3 | `breachedaccount` endpoint | Needs a subscription/test key (`hibp_api_key`, 32 hex). Terms: send a descriptive user-agent; respect 429 `retry-after` |
