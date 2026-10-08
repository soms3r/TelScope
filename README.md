<div align="center">

# 🔭 TelScope

**One sweep. Every signal.**

*A unified, local-first OSINT dashboard for phone numbers & emails — six battle-tested tools, one clean interface.*

[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab.svg?logo=python&logoColor=white)](https://www.python.org)
[![Release](https://img.shields.io/github/v/release/soms3r/TelScope?label=release&color=0ea5e9)](https://github.com/soms3r/TelScope/releases)
[![Website](https://img.shields.io/badge/site-soms3r.github.io%2FTelScope-8b5cf6.svg)](https://soms3r.github.io/TelScope/)

</div>

> ⚖️ **Ethics & legality — read before use.** TelScope is for **authorized investigations only**: your own numbers, targets you have written permission to investigate, or legitimate security research. It touches only publicly available data and platform registration flows. **No warranty, no liability — you are responsible for how you use it.** Full rules: [TERMS.md](TERMS.md) · [PRIVACY.md](PRIVACY.md).

---

## What is TelScope?

TelScope wraps the six best open-source phone/email OSINT tools behind one dark, fast web dashboard. Type a number (any country, auto-normalized to E.164) or an email, pick your modules, hit **RUN SWEEP** — and watch carrier intel, platform footprints and spam reputation stream in live, merged into a single intelligence view you can export as JSON / CSV / HTML report.

<!-- TODO(M5): add docs/images/demo.gif -->

## ✨ Features

| | |
|---|---|
| 🌍 **Global input** | Any country's phone number, normalized to E.164 (Google libphonenumber) — or an email address |
| 🧩 **Six modules** | Toggleable adapters with per-module health checks and graceful degradation |
| ⚡ **Live sweep** | Concurrent execution, streamed logs, per-module timers, one-click cancel |
| 🧠 **Merged intelligence** | Carrier / line type / region, platform registrations, spam reputation, footprint links |
| 🗂 **History & exports** | Local SQLite history; JSON / CSV / printable HTML report |
| 🔒 **Local-first & private** | Binds to `127.0.0.1` only, zero telemetry, zero accounts — [privacy promise](PRIVACY.md) |

## 🧰 Modules & credits

TelScope stands on the shoulders of these open-source tools — **all credit to their authors**:

| Module | What it adds | Author | License | Repo |
|---|---|---|---|---|
| PhoneInfoga | Carrier, line type, country, web footprint | sundowndev | GPL-3.0 | [sundowndev/phoneinfoga](https://github.com/sundowndev/phoneinfoga) |
| Ignorant | Silent platform-registration check (Instagram, Snapchat, Amazon…) | megadose | GPL-3.0 | [megadose/ignorant](https://github.com/megadose/ignorant) |
| Moriarty / Gökbörü | Unified phone investigation (owner hints, spam risk, socials) | AzizKpln | MIT | [AzizKpln/Gokboru_Intel](https://github.com/AzizKpln/Gokboru_Intel) |
| email2phonenumber | Email → phone fragments via recovery flows *(experimental)* | Martin Vigo | MIT | [martinvigo/email2phonenumber](https://github.com/martinvigo/email2phonenumber) |
| X-osint | Phone / email / VIN / reverse-lookup framework (Termux-born) | TermuxHackz | GPL-3.0 | [TermuxHackz/X-osint](https://github.com/TermuxHackz/X-osint) |
| Phomber | Carrier + spam / fraud reputation intel | s41r4j | GPL-3.0 | [s41r4j/phomber](https://github.com/s41r4j/phomber) |

TelScope runs GPL-3.0 tools strictly as **separate processes** (subprocess or their own REST API) and ships none of their code — see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## 🚀 Quick start

**Option A — release zip (recommended):**
1. Download [`TelScope-v1.0.zip`](https://github.com/soms3r/TelScope/releases/latest/download/TelScope-v1.0.zip) and verify against `SHA256SUMS` on the [releases page](https://github.com/soms3r/TelScope/releases).
2. Extract anywhere.
3. Double-click `run.bat` (Windows) or `./run.sh` (Linux / macOS). Your browser opens `http://127.0.0.1:8000`.

The first run provisions pinned tool binaries/repos automatically (internet required once).

**Option B — from source:**

```bash
git clone https://github.com/soms3r/TelScope && cd TelScope
# Windows: run.bat   ·   Linux/macOS: ./run.sh
```

Requires **Python 3.10+**. That's it.

<!-- TODO(M5): screenshots — dashboard / execution / results / export -->

## 🔒 Privacy in five bullets

- Binds to **localhost only** — no exposure, no auth needed.
- **No telemetry, no analytics, no cookies, no accounts, no phone-home.**
- History lives in a SQLite file **inside your folder**; *Clear history* deletes it all.
- Queries travel from **your machine** directly to public sources.
- Setup downloads tools from their **official repos**, pinned and checksummed.

## 🙏 Credits

Developed by **[@soms3r](https://github.com/soms3r)** · built on the six tools above · inspired by the OSINT community.

Platform names (Instagram, Snapchat, Amazon, …) are trademarks of their respective owners. TelScope is **not affiliated with or endorsed by** them or any queried platform.

## 📄 License

MIT © 2026 soms3r — see [LICENSE](LICENSE). Third-party components keep their own licenses ([notices](THIRD-PARTY-NOTICES.md)).
