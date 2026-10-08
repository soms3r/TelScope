# Third-Party Notices

TelScope (MIT, © 2026 soms3r) **wraps** the open-source tools below. They remain
independent programs with their own licenses, authors, and repositories. TelScope
communicates with them only across process boundaries (CLI subprocesses or their
own local REST APIs) and **does not copy, link, or statically import GPL-licensed
code** into its codebase.

## Components

| Component | Author | License | Source | Role in TelScope |
|---|---|---|---|---|
| PhoneInfoga | sundowndev | GPL-3.0 | <https://github.com/sundowndev/phoneinfoga> | Carrier / line-type / country + web footprint (via its local REST API) |
| Ignorant | megadose | GPL-3.0 | <https://github.com/megadose/ignorant> | Silent platform-registration checks (via CLI subprocess) |
| Moriarty / Gökbörü Intelligence | AzizKpln | MIT | <https://github.com/AzizKpln/Gokboru_Intel> | Unified phone investigation (via CLI subprocess) |
| email2phonenumber | Martin Vigo | MIT | <https://github.com/martinvigo/email2phonenumber> | Email → phone fragments, experimental (vendored pinned script, license retained) |
| X-osint | TermuxHackz | GPL-3.0 | <https://github.com/TermuxHackz/X-osint> | Phone / email / VIN / reverse lookups (via CLI subprocess) |
| Phomber | s41r4j | GPL-3.0 | <https://github.com/s41r4j/phomber> | Carrier + spam / fraud reputation (via CLI subprocess) |

Python runtime dependencies (FastAPI, uvicorn, httpx, phonenumbers, pydantic, …)
are used under their respective permissive licenses and listed in
`requirements.txt` with pins.

## Version pins

Exact pinned versions / commits and SHA-256 checksums used by `bootstrap.py` are
recorded in `PINS.md` (generated during the M0 integration spike) and echoed in
every release's notes.

## Distribution policy

- The release zip contains **only TelScope's own MIT-licensed code** and docs.
- Third-party tools are downloaded **by the user's machine at first run**, from
  the official sources above, at pinned versions with checksum verification.
- MIT-licensed `email2phonenumber` is vendored as a pinned git submodule with its
  license retained, as permitted by the MIT license.

## Trademarks

Platform and service names (Instagram, Snapchat, Amazon, Truecaller, …) are
trademarks of their respective owners. TelScope is not affiliated with or
endorsed by them.

## Licenses (full texts)

Full license texts for GPL-3.0 and MIT are available at
<https://www.gnu.org/licenses/gpl-3.0.html> and
<https://opensource.org/license/mit>. Each component's repository contains its
authoritative license file.
