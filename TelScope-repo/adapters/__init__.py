"""Adapter registry (MIT). Order = UI order."""
from .phoneinfoga import PhoneInfogaAdapter
from .ignorant import IgnorantAdapter
from .moriarty import MoriartyAdapter
from .email2phone import Email2PhoneAdapter
from .xosint import XosintAdapter
from .phomber import PhomberAdapter

ALL_ADAPTERS = [
    PhoneInfogaAdapter(),
    IgnorantAdapter(),
    MoriartyAdapter(),
    Email2PhoneAdapter(),
    XosintAdapter(),
    PhomberAdapter(),
]

__all__ = ["ALL_ADAPTERS"]
