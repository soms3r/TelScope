# Changelog

## v2.0.0 — 2026-10-08

**Twelve modules** (was six).

### Added
- `phonemeta` — offline phone metadata (validity, line type, region, timezones, prefix carrier).
- `emailcheck` — domain MX/A records and disposable-provider flag (no mailbox probing).
- `emaildns` — SPF / DMARC / common DKIM selector posture for the email's domain.
- `domainrdap` — domain registrar, dates, nameservers, status via RDAP (no registrant data; free-mail skipped).
- `hibp` — breach exposure via HIBP API v3 (needs `hibp_api_key`).
- `hibp_pastes` — paste exposure via HIBP API v3 (metadata only, needs `hibp_api_key`).
- **Audit log**: every sweep recorded with keyed hashes of identifiers; readable at `/api/audit`; survives "clear history".
- Settings: HIBP API key field.
- Offline test suite (`tests/`, 19 tests, recorded fixtures).
- `breach` finding type and a "breach exposure" results card.
- Consent text now covers breach-check scope and the audit log.
- `dnspython` added to requirements.

### Changed
- App version 2.0.0; readiness counter reads the module count from the server.
- Consent modal clarifies that breach checks are for identifiers you own or are authorized to check.
- Website and README updated to v2.0.

### Unchanged
- The six wrapped tools, their pins, the separation doctrine (GPL tools as separate processes), and the localhost-only bind.

## v1.0.0 — 2026-10-08
- Initial release: six wrapped OSINT tools behind one dashboard, live sweeps, history, JSON/CSV/HTML exports.
