# TelScope Privacy Policy

*Short version: TelScope is local-first software. It has no servers, no telemetry,
no analytics, no cookies, no accounts, and no way to phone home. Your data never
leaves your machine except for the queries the wrapped tools make to public
sources — directly from your IP, under your control.*

## 1. What TelScope stores, and where

All data is stored **only on your device**, inside the folder where you extracted
TelScope:

- `telscope.db` (SQLite) — investigation history: targets you swept, aggregated
  findings, per-module raw output, timestamps, and your settings (default region,
  timeouts, module toggles) plus the first-run consent flag.
- Exported reports you explicitly create (`reports/`).

Nothing is uploaded, synced, or shared with the TelScope developer. The developer
**cannot** see your history — it never leaves your machine.

## 2. What leaves your machine (and why)

- **OSINT queries.** When you run a sweep, the wrapped tools contact publicly
  available sources and platform endpoints from **your** machine and **your** IP
  address. This is inherent to what the tools do; see each tool's own repository
  for its behaviour.
- **One-time setup downloads.** `bootstrap.py` downloads pinned releases of the
  wrapped tools from their official GitHub repositories / PyPI so the app can run.
  No personal data is sent; standard download requests only.

That is all. There is no telemetry, no crash reporting, no analytics, no
update-check beacon.

## 3. What the website stores

The project site (GitHub Pages) is **static HTML/CSS**: no cookies, no trackers,
no analytics, no comment systems. GitHub itself serves the pages and applies its
own privacy policy to page delivery (e.g. IP address in server logs).

## 4. Your controls

- **Clear history** button in the UI deletes all jobs/findings from the database.
- Deleting the TelScope folder deletes everything else (settings, exports, DB).
- Module toggles let you limit which tools run for a sweep.
- The aggressive `bruteforce` mode of email2phonenumber is **off by default** and
  requires explicit per-run opt-in plus proxy configuration.

## 5. Your responsibility

Investigate only targets you are authorized to investigate. Raw outputs stored in
history may contain personal data about third parties — keep the folder private
and clear history when done.

## 6. Changes & contact

Material changes to this policy will be noted in the repository changelog.
Questions: open an issue at <https://github.com/soms3r/TelScope> or use
[SECURITY.md](SECURITY.md) for sensitive matters.

*This document is best-practice positioning for a local-first tool, not legal advice.*
