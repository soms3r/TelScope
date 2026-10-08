# Integration Notes (M0 spike, executed 2026-10-08 in a Linux x86_64 sandbox)

Every statement below was produced by actually running the tool. Pins live in `PINS.md`.

## 1. PhoneInfoga (sundowndev, GPL-3.0) — REST API driver
- Binary v2.11.0 downloaded from GitHub Releases; `sha256sum -c` against official
  `phoneinfoga_checksums.txt` → OK.
- Server: `phoneinfoga serve --no-client -p 5001` (adapter auto-starts it).
- **Real routes (discovered by probing the binary; the docs 404):**
  - `GET  /api/` → `{"success":true,"version":"2.11.0",...}`
  - `GET  /api/v2/scanners` → list (`local`, `numverify`, `googlesearch`, `ovh`, …)
  - `POST /api/v2/scanners/{name}/run` body `{"number":"<digits WITHOUT +>"}` → `{"result":{...}}`
  - Numbers WITH `+` are rejected: `400 Invalid phone number: please provide an integer...`
- Verified outputs: `local` → e164/country_code/local formats; `googlesearch` → social-media
  dork URLs (used as `link` findings); `ovh` → VoIP-range hit; `numverify` needs API key (optional setting).

## 2. Ignorant (megadose, GPL-3.0) — CLI subprocess
- `pip install ignorant` (v1.2). Command: `ignorant <cc> <national> --no-color --no-clear -T 10`.
- Output grammar (verified): `[+] domain` registered · `[-] domain` not used · `[x] domain` rate-limited.
- Sandbox IP got `[x]` on all three platforms (shared egress) — rate-limit path exercised and surfaced as UI warnings.

## 3. Phomber (s41r4j, GPL-3.0) — pty-driven REPL
- `pip install phomber` (3.1.1). Crashes without a TTY (`os.get_terminal_size`), **unless** `-s/--silent`.
- Even silent, piped stdin produces nothing (prompt_toolkit). Solution verified: run through a
  pseudo-terminal (`script -qec` in spike; `os.openpty()` in the adapter):
  `printf 'number +E164\nexit\n' | <pty> phomber -s` → INFORMATION/DESCRIPTION table
  (Possible/Valid, and for valid numbers carrier/timezone/region rows — 8 findings on +44 test).
- POSIX-only: adapter reports `unavailable` on Windows.

## 4. Moriarty — TWO projects share the name (resolved)
- **PyPI `moriarty-project` (0.1.27) is a DIFFERENT tool**: a Portuguese typer CLI for
  dns/email/rdap/tls/user/IOC intelligence; also broken out of the box against current
  `selectolax` (needs `selectolax<1.0` pin). **Not used by TelScope.**
- The phone tool is **AzizKpln/Gokboru_Intel** (repo renamed from Moriarty-Project; actively
  maintained; MIT). CLI verified from `CLI-USAGE.md`:
  `bash ./moriarty-local phone-audit "+E164" --i-own-this-number --sources local,reputation --timeout N --output out.json`
  (consent flag built in — matches our ethics gate).
- `moriarty-local` requires a one-time GUI installer (`install.sh`, refuses root, needs python3-tk).
  Adapter degrades fast with exactly that hint until the user runs it once. Browser sources need `xvfb-run`.

## 5. email2phonenumber (martinvigo, MIT) — vendored script, experimental
- `python3 email2phonenumber.py scrape -e <email>` — author's README already warns original
  services added captchas; in sandbox the first service DNS-fails with a traceback.
- Adapter is crash-tolerant: partial `Scraping X` progress + digit-fragment/masked-number regexes;
  tracebacks become warnings; status stays honest. **`bruteforce` mode is never invoked.**

## 6. X-osint (TermuxHackz, GPL-3.0) — assisted-manual (plan §16 contingency)
- Imports tkinter/prompt_toolkit/flask/stripe, disclaimer file, interactive menus; reliable
  non-interactive driving not feasible → adapter returns `manual` with exact steps;
  UI ingests pasted output via `POST /api/jobs/{id}/manual` (verified working).

## 7. End-to-end verification (sandbox, 2026-10-08)
- `POST /api/consent`, `POST /api/sweep` for `+1 555 019 2834`, `+442079460918`, `test@example.com`.
- Jobs reached `done`; SSE stream, per-module cards, exports (json/csv/html), history,
  settings roundtrip and manual-paste all exercised via curl against the running app.
- PhoneInfoga REST server lifecycle (auto-start + shutdown hook) verified.

## 8. Consequences baked into code
- Ignorant regex includes the opening bracket (`\[([+\-x])\]`) — the first spike build missed it.
- PhoneInfoga numbers sent without `+`.
- Moriarty health checks the v5 venv path (`$XDG_DATA_HOME|~/.local/share`/moriarty-v5/venv).
- All GPL tools remain separate processes (subprocess / pty / own REST server) — separation doctrine.
