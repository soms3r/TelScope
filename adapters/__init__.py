"""Adapter registry (MIT). Order = UI order. v2.0: 12 modules."""
# existing six (phone/email wrappers)
from .phoneinfoga import PhoneInfogaAdapter
from .ignorant import IgnorantAdapter
from .moriarty import MoriartyAdapter
from .email2phone import Email2PhoneAdapter
from .xosint import XosintAdapter
from .phomber import PhomberAdapter
# v2.0 additions (built-in, MIT, public data / DNS / official APIs only)
from .phonemeta import PhoneMetaAdapter
from .emailcheck import EmailCheckAdapter
from .emaildns import EmailDNSAdapter
from .domainrdap import DomainRDAPAdapter
from .hibp import HIBPAdapter, HIBPPastesAdapter

ALL_ADAPTERS = [
    PhoneMetaAdapter(),
    PhoneInfogaAdapter(),
    IgnorantAdapter(),
    MoriartyAdapter(),
    Email2PhoneAdapter(),
    XosintAdapter(),
    PhomberAdapter(),
    EmailCheckAdapter(),
    EmailDNSAdapter(),
    DomainRDAPAdapter(),
    HIBPAdapter(),
    HIBPPastesAdapter(),
]

__all__ = ["ALL_ADAPTERS"]
