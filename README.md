<div align="center">

# 🔭 TelScope

**One sweep. Every signal.**

*A unified, local-first OSINT dashboard for phone numbers & emails — **twelve modules**, one clean interface.*

[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab.svg?logo=python&logoColor=white)](https://www.python.org)
[![Release](https://img.shields.io/github/v/release/soms3r/TelScope?label=release&color=0ea5e9)](https://github.com/soms3r/TelScope/releases)
[![Website](https://img.shields.io/badge/site-soms3r.github.io%2FTelScope-8b5cf6.svg)](https://soms3r.github.io/TelScope/)

</div>

> ⚖️ **Ethics & legality — read before use.** TelScope is for **authorized investigations only**: your own numbers or emails, targets you have written permission to investigate, or legitimate security research. It touches only public data, DNS records, official breach-notification APIs and platform registration flows. **No warranty, no liability — you are responsible for how you use it.** Full rules: [TERMS.md](TERMS.md) · [PRIVACY.md](PRIVACY.md).

---

## What is TelScope?

TelScope wraps the best open-source phone/email OSINT tools — and adds its own checks — behind one dark, fast web dashboard. Type a number (any country, auto-normalized to E.164) or an email, pick your modules, hit **RUN SWEEP**, and watch carrier intel, platform footprints, mail-domain posture, breach exposure and domain registration stream in live. Everything is merged into one intelligence view you can export as JSON / CSV / HTML report.

## ✨ Features

| | |
|---|---|
| 🌍 **Global input** | Any country's phone number, normalized to E.164 (Google libphonenumber) — or an email address |
| 🧩 **Twelve modules** | Six wrapped open-source tools + six built-in checks, each with health status and graceful degradation |
| ⚡ **Live sweep** | Concurrent execution, streamed logs, per-module timers, one-click cancel |
| 🧠 **Merged intelligence** | Carrier / line type / region, platform registrations, breach exposure, mail-security posture, domain registration, footprint links |
| 📜 **Audit log** (new in v2.0) | Every sweep is recorded locally (time, job, modules, consent time) — identifiers stored only as keyed hashes |
| 🗂 **History & exports** | Local SQLite history; JSON / CSV / printable HTML report |
| 🔒 **Local-first & private** | Binds to `127.0.0.1` only, zero telemetry, zero accounts — [privacy promise](PRIVACY.md) |

## 🧰 The twelve modules

### Wrapped open-source tools (v1.0)

TelScope runs these as **separate processes** (subprocess or their own REST API) and ships none of their code. All credit to their authors:

| Module | What it adds | Author | License | Repo |
|---|---|---|---|---|
| `phoneinfoga` | Carrier, line type, country, web footprint | sundowndev | GPL-3.0 | [sundowndev/phoneinfoga](https://github.com/sundowndev/phoneinfoga) |
| `ignorant` | Silent platform-registration check (Instagram, Snapchat, Amazon…) | megadose | GPL-3.0 | [megadose/ignorant](https://github.com/megadose/ignorant) |
| `moriarty` | Unified phone investigation (owner hints, spam risk, socials) | AzizKpln | MIT | [AzizKpln/Gokboru_Intel](https://github.com/AzizKpln/Gokboru_Intel) |
| `email2phone` | Email → phone fragments via recovery flows *(experimental)* | Martin Vigo | MIT | [martinvigo/email2phonenumber](https://github.com/martinvigo/email2phonenumber) |
| `xosint` | Phone / email / VIN / reverse-lookup framework | TermuxHackz | GPL-3.0 | [TermuxHackz/X-osint](https://github.com/TermuxHackz/X-osint) |
| `phomber` | Carrier + spam / fraud reputation intel | s41r4j | GPL-3.0 | [s41r4j/phomber](https://github.com/s41r4j/phomber) |

### Built-in checks (new in v2.0)

These are TelScope's own adapters (MIT). They use only offline metadata, DNS records, or official public APIs:

| Module | Input | What it checks | Data source |
|---|---|---|---|
| `phonemeta` | phone | Validity, line type (mobile / fixed / VoIP…), region, timezones, prefix-based carrier. **Fully offline.** | [phonenumbers](https://github.com/daviddrysdale/python-phonenumbers) (libphonenumber port, Apache-2.0) |
| `emailcheck` | email | Domain MX/A records, disposable-mail provider flag. **No mailbox probing.** | DNS (via [dnspython](https://www.dnspython.org/), ISC) |
| `emaildns` | email | Domain mail-security posture: SPF strictness, DMARC policy, common DKIM selectors | DNS TXT records |
| `domainrdap` | email | Domain registrar, registration/expiry dates, nameservers, status. Contact/registrant fields are never read; free-mail domains are skipped. | RDAP via [rdap.org](https://rdap.org) |
| `hibp` | email | Breaches the address appears in (date + data classes). Needs your HIBP key. | [Have I Been Pwned](https://haveibeenpwned.com) API v3 by Troy Hunt |
| `hibp_pastes` | email | Pastes that list the address (source, date, count — **no paste content**). Needs your HIBP key. | Have I Been Pwned API v3 |

TelScope uses the HIBP API under its terms: your key is sent only in the `hibp-api-key` header, and the user-agent identifies the app. Breach dumps and credentials are never downloaded or stored.

See [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) for full license information.

## 🚀 Quick start

**Option A — release zip (recommended):**
1. Download [`TelScope-v2.0.0.zip`](https://github.com/soms3r/TelScope/releases/latest/download/TelScope-v2.0.0.zip) and verify it against `SHA256SUMS` on the [releases page](https://github.com/soms3r/TelScope/releases).
2. Extract anywhere.
3. Double-click `run.bat` (Windows) or `./run.sh` (Linux / macOS). Your browser opens `http://127.0.0.1:8000`.

The first run provisions pinned tool binaries/repos automatically (internet required once). The built-in checks need no setup.

**Option B — from source:**

```bash
git clone https://github.com/soms3r/TelScope && cd TelScope
# Windows: run.bat   ·   Linux/macOS: ./run.sh
```

Requires **Python 3.10+**.

### Enabling breach checks (HIBP)

1. Get a key at [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key) (paid subscription, or a free test key that works on limited test addresses).
2. In TelScope, open **⚙ settings** → paste it into **HIBP API key** → save.
3. The `hibp` and `hibp_pastes` modules turn ready. Without a key they show as *missing*; nothing else is affected.

## 🛡 Audit log

Every sweep writes one row to a local audit table: timestamp, job ID, module list, the time consent was granted, and a **keyed HMAC-SHA-256 hash** of the identifier. The raw number or email is never stored in the audit log, and clearing history does **not** clear it.

View it in your browser at `http://127.0.0.1:8000/api/audit` (read-only JSON).

## 🔒 Privacy in five bullets

- Binds to **localhost only** — no exposure, no auth needed.
- **No telemetry, no analytics, no cookies, no accounts, no phone-home.**
- History and audit log live in a SQLite file **inside your folder**; *Clear history* deletes the history.
- Queries travel from **your machine** directly to public sources, DNS, RDAP or HIBP.
- Setup downloads tools from their **official repos**, pinned and checksummed.

## 🧪 Testing

The test suite is fully offline (HTTP and DNS are mocked with recorded fixtures):

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md). Version 2.0.0 adds six modules, the audit log and the HIBP key setting.

## 🙏 Credits

Developed by **[@soms3r](https://github.com/soms3r)** · built on the open-source tools above · inspired by the OSINT community.

Platform names (Instagram, Snapchat, Amazon, …) are trademarks of their respective owners. TelScope is **not affiliated with or endorsed by** them or any queried platform.

## 📄 License

MIT © 2026 soms3r — see [LICENSE](LICENSE). Third-party components keep their own licenses ([notices](THIRD-PARTY-NOTICES.md)).
