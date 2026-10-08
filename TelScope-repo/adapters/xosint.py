"""X-osint adapter — ASSISTED MANUAL mode (per plan §16 contingency).

X-osint is interactive (prompt_toolkit menus + tkinter GUI parts); reliable
non-interactive driving is not feasible. TelScope therefore presents the exact
steps and ingests the pasted raw output into the unified schema via
POST /api/jobs/{id}/manual.
"""
from __future__ import annotations

from core.schema import ModuleResult

from .base import Adapter, REPO_ROOT

VENDOR = REPO_ROOT / "vendor" / "X-osint"

STEPS = [
    "X-osint is interactive — TelScope runs it in assisted-manual mode:",
    "1) cd vendor/X-osint && python3 xosint   (accept the disclaimer once)",
    "2) pick the phone-number module and enter the target",
    "3) copy the printed result and paste it into this module's box in the UI",
]


class XosintAdapter(Adapter):
    name = "xosint"
    inputs = {"phone", "email"}
    timeout_s = 30

    async def health(self) -> dict:
        if not (VENDOR / "xosint").exists():
            return {"available": False,
                    "detail": "vendor missing — run bootstrap.py (clones X-osint)"}
        return {"available": True, "detail": "TermuxHackz/X-osint · assisted-manual mode"}

    async def run(self, target, ctx) -> ModuleResult:
        if not (VENDOR / "xosint").exists():
            return ModuleResult(module=self.name, status="unavailable",
                                warnings=["vendor/X-osint missing"])
        ctx.log("xosint: awaiting assisted-manual input")
        return ModuleResult(
            module=self.name, status="manual",
            warnings=list(STEPS) + [f"Target for this run: {target.raw}"],
        )
