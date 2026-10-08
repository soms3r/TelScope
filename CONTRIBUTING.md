# Contributing to TelScope

Contributions are welcome — bug fixes, new adapters, parsers, translations, docs.

## Ground rules

1. Be respectful (see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)).
2. Keep PRs focused; describe what and why.
3. Test against **safe targets only**: fictional reserved numbers
   (`+1 555 01xx xxxx`), `@example.com` emails, or accounts you own.

## New module / adapter checklist

A new integration will only be accepted if it passes **all** of these:

- [ ] **Public data only** — no breached dumps, no PII brokers, no credential use.
- [ ] **No unauthorized access** — no auth bypass, no scraping behind login, no
      contacting the target (no SMS/calls triggered).
- [ ] **License-compatible** — permissive (MIT/BSD/Apache) code may be imported;
      **GPL/AGPL code must run as a separate process** (subprocess or its own
      REST API), never imported into TelScope's codebase (separation doctrine,
      see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)).
- [ ] **Attribution** — author, repository, and license added to
      THIRD-PARTY-NOTICES.md, README, and the website credits page.
- [ ] **Version pin** — exact version/commit + checksum recorded for bootstrap.
- [ ] **Adapter contract** — implements `health()` and `run()` returning the
      unified `ModuleResult` schema; never raises; degrades to `unavailable`.
- [ ] **Fixture test** — parser unit-tested against a recorded output fixture.

## Code style

- Python 3.10+, type hints on adapter boundaries, `ruff` clean.
- Frontend: vanilla JS + Tailwind (CDN with bundled fallback CSS); no build step.

## Pull request flow

Fork → branch → PR against `main` → CI green → review. By contributing you agree
your work is licensed under the project's MIT license.
