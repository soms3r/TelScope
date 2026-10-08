"""Offline tests for TelScope v2.0 modules. No network: HTTP and DNS are mocked
with recorded fixtures (see tests/fixtures). Run:  python -m pytest -q"""
import asyncio
import json
import sqlite3
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters import ALL_ADAPTERS  # noqa: E402
from adapters import base as adapter_base  # noqa: E402
from adapters import domainrdap, emaildns, emailcheck, hibp  # noqa: E402
from adapters.base import Ctx  # noqa: E402
from core.normalize import parse_target  # noqa: E402
from core.store import Store  # noqa: E402

FIX = Path(__file__).parent / "fixtures"
KEY = "ab" * 16


def run(adapter, target):
    return asyncio.run(adapter.run(target, Ctx({}, lambda _l: None)))


def by_name(name):
    return next(a for a in ALL_ADAPTERS if a.name == name)


@pytest.fixture
def key(monkeypatch):
    monkeypatch.setattr(adapter_base, "settings_provider", lambda: {"hibp_api_key": KEY})
    return KEY


def mock_http(monkeypatch, handler):
    """Route every httpx.AsyncClient created by an adapter through a MockTransport."""
    real = httpx.AsyncClient

    class Mock(real):
        def __init__(self, *a, **k):
            k["transport"] = httpx.MockTransport(handler)
            super().__init__(*a, **k)

    monkeypatch.setattr(hibp.httpx, "AsyncClient", Mock)
    monkeypatch.setattr(domainrdap.httpx, "AsyncClient", Mock)


# ---------------------------------------------------------------- registry
def test_twelve_modules_registered():
    names = [a.name for a in ALL_ADAPTERS]
    assert len(names) == 12 and len(set(names)) == 12
    for n in ["phonemeta", "emailcheck", "emaildns", "domainrdap", "hibp", "hibp_pastes"]:
        assert n in names


# ---------------------------------------------------------------- phone (offline)
def test_phonemeta_uk_fixed_line():
    t = parse_target("+442079460918", "BD")
    r = run(by_name("phonemeta"), t)
    assert r.status == "ok"
    vals = {f.key: f.value for f in r.findings}
    assert vals["number validity"] == "valid"
    assert vals["line type"] == "fixed line"
    assert vals["region"] == "London"


# ---------------------------------------------------------------- email DNS
def test_spf_dmarc_parsers():
    assert emaildns.parse_spf("v=spf1 include:_spf.google.com -all")[1] == "strict (hard fail)"
    assert emaildns.parse_spf("v=spf1 +all")[1].startswith("open")
    assert emaildns.parse_spf("v=spf1 ip4:1.2.3.4")[1].startswith("no all")
    assert emaildns.parse_dmarc("v=DMARC1; p=REJECT; rua=mailto:x@y") == "reject"
    assert emaildns.parse_dmarc("v=DMARC1; p=none") == "none"


def test_emaildns_full_posture(monkeypatch):
    table = {
        "example.org": ["v=spf1 include:_spf.example.org -all"],
        "_dmarc.example.org": ["v=DMARC1; p=quarantine; pct=100"],
        "google._domainkey.example.org": ["v=DKIM1; k=rsa; p=MIIBIjANBg"],
    }

    def fake_query(domain, rtype):
        if domain in table:
            class R:  # mimic dnspython TXT answer objects
                def __init__(self, s): self.strings = [s.encode()]
            return [R(s) for s in table[domain]]
        raise emailcheck.dns.resolver.NXDOMAIN()

    monkeypatch.setattr(emaildns, "query_dns", fake_query)
    r = run(by_name("emaildns"), parse_target("alice@example.org", "BD"))
    vals = {f.key: f.value for f in r.findings}
    assert vals["SPF"].startswith("strict")
    assert vals["DMARC policy"] == "quarantine"
    assert vals["DKIM selectors found"] == "google"
    assert r.warnings == []


def test_emaildns_warns_on_open_spf_and_dmarc_none(monkeypatch):
    def fake_query(domain, rtype):
        class R:
            def __init__(self, s): self.strings = [s.encode()]
        if domain == "weak.example":
            return [R("v=spf1 +all")]
        if domain == "_dmarc.weak.example":
            return [R("v=DMARC1; p=none")]
        raise emailcheck.dns.resolver.NXDOMAIN()

    monkeypatch.setattr(emaildns, "query_dns", fake_query)
    r = run(by_name("emaildns"), parse_target("bob@weak.example", "BD"))
    assert any("+all" in w for w in r.warnings)
    assert any("p=none" in w for w in r.warnings)


# ---------------------------------------------------------------- email MX
def test_classify_domain_states():
    assert emailcheck.classify_domain(["mx.x.com"], None) == "accepts mail (MX present)"
    assert emailcheck.classify_domain(None, True).startswith("no MX; A record only")
    assert emailcheck.classify_domain(None, None, nxdomain=True) == "domain does not exist"


def test_emailcheck_disposable(monkeypatch):
    class MX:
        def __init__(self, h): self.exchange = h
    monkeypatch.setattr(emailcheck, "query_dns",
                        lambda d, t: [MX("mail.mailinator.com.")])
    r = run(by_name("emailcheck"), parse_target("x@mailinator.com", "BD"))
    vals = {f.key: f.value for f in r.findings}
    assert vals["disposable provider"].startswith("yes")
    assert vals["mail servers (MX)"] == "mail.mailinator.com"


# ---------------------------------------------------------------- RDAP
def test_rdap_parser_reads_registrar_not_registrant():
    doc = json.loads((FIX / "rdap_example.json").read_text())
    findings = domainrdap.parse_rdap(doc)
    text = " ".join(f"{f.key}={f.value}" for f in findings)
    assert "registered=1995-08-14" in text
    assert "registrar=Example Registrar, Inc." in text
    assert "A.IANA-SERVERS.NET" not in text  # ns are lower-cased
    assert "PRIVATE PERSON" not in text and "private@example.net" not in text


def test_rdap_skips_free_mail(monkeypatch):
    monkeypatch.setattr(domainrdap.httpx, "AsyncClient",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no request")))
    r = run(by_name("domainrdap"), parse_target("someone@gmail.com", "BD"))
    assert r.findings == [] and "free-mail" in r.warnings[0]


def test_rdap_http_flow(monkeypatch):
    doc = (FIX / "rdap_example.json").read_text()
    mock_http(monkeypatch, lambda req: httpx.Response(200, text=doc,
                                                      headers={"content-type": "application/rdap+json"}))
    r = run(by_name("domainrdap"), parse_target("ops@example.org", "BD"))
    assert r.status == "ok" and any(f.key == "registrar" for f in r.findings)


# ---------------------------------------------------------------- HIBP
def test_hibp_health_needs_valid_key(monkeypatch):
    monkeypatch.setattr(adapter_base, "settings_provider", lambda: {"hibp_api_key": ""})
    assert asyncio.run(by_name("hibp").health())["available"] is False
    monkeypatch.setattr(adapter_base, "settings_provider", lambda: {"hibp_api_key": "nothex"})
    assert "32 hex" in asyncio.run(by_name("hibp").health())["detail"]


def test_hibp_breaches_parse_and_headers(monkeypatch, key):
    seen = {}

    def handler(req):
        seen["key"] = req.headers.get("hibp-api-key")
        seen["ua"] = req.headers.get("user-agent")
        seen["url"] = str(req.url)
        return httpx.Response(200, text=(FIX / "hibp_breaches.json").read_text())

    mock_http(monkeypatch, handler)
    r = run(by_name("hibp"), parse_target("alice@example.org", "BD"))
    assert r.status == "ok" and len(r.findings) == 2
    assert r.findings[0].type == "breach" and r.findings[0].key == "Adobe"
    assert "2013-10-04" in r.findings[0].value
    assert seen["key"] == KEY and seen["ua"].startswith("TelScope/2.0")
    assert "truncateResponse=false" in seen["url"]


@pytest.mark.parametrize("status,expect_status", [(404, "ok"), (401, "error"), (429, "error"), (500, "error")])
def test_hibp_status_handling(monkeypatch, key, status, expect_status):
    mock_http(monkeypatch, lambda req: httpx.Response(status, headers={"retry-after": "7"}))
    r = run(by_name("hibp"), parse_target("alice@example.org", "BD"))
    assert r.status == expect_status and r.findings == []


def test_hibp_paste_parse(monkeypatch, key):
    mock_http(monkeypatch, lambda req: httpx.Response(200, text=(FIX / "hibp_pastes.json").read_text()))
    r = run(by_name("hibp_pastes"), parse_target("alice@example.org", "BD"))
    assert r.findings[0].key == "paste · Pastebin"
    assert "2 addresses" in r.findings[0].value


def test_hibp_unavailable_without_key(monkeypatch):
    monkeypatch.setattr(adapter_base, "settings_provider", lambda: {})
    r = run(by_name("hibp_pastes"), parse_target("alice@example.org", "BD"))
    assert r.status == "unavailable"


# ---------------------------------------------------------------- audit log
def test_audit_hashes_identifier_and_survives_clear(tmp_path):
    st = Store(tmp_path / "t.db")
    t = parse_target("alice@example.org", "BD")
    st.log_audit("job1", t, ["hibp", "emaildns"])
    st.clear_history()
    rows = st.list_audit()
    assert len(rows) == 1 and rows[0]["modules"] == ["hibp", "emaildns"]
    assert "alice" not in json.dumps(rows)                 # no raw identifier stored
    assert len(rows[0]["target_hash"]) == 64
    with sqlite3.connect(tmp_path / "t.db") as c:
        raw = c.execute("SELECT group_concat(target_hash) FROM audit").fetchone()[0]
    assert "example.org" not in raw


def test_clear_audit(tmp_path):
    st = Store(tmp_path / "t.db")
    st.log_audit("job2", parse_target("+442079460918", "BD"), ["phonemeta"])
    st.clear_audit()
    assert st.list_audit() == []
