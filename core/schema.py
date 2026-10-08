"""TelScope unified data model (MIT)."""
from __future__ import annotations

import time
import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field

Status = Literal["ok", "error", "timeout", "unavailable", "manual"]
FindingType = Literal[
    "carrier", "line_type", "region", "platform",
    "spam_score", "link", "owner_hint", "validity", "raw", "breach",
]
Confidence = Literal["high", "medium", "low"]


class Target(BaseModel):
    type: Literal["phone", "email"]
    raw: str
    e164: Optional[str] = None
    country_code: Optional[int] = None
    national: Optional[str] = None
    region: Optional[str] = None
    email: Optional[str] = None


class Finding(BaseModel):
    type: FindingType
    key: str = ""
    value: str = ""
    confidence: Confidence = "medium"
    source: str = ""
    observed_at: float = Field(default_factory=time.time)


class ModuleResult(BaseModel):
    module: str
    status: Status
    duration_s: float = 0.0
    findings: list[Finding] = []
    warnings: list[str] = []
    raw_log: str = ""


class Job(BaseModel):
    job_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = Field(default_factory=time.time)
    target: Target
    status: Literal["running", "done", "cancelled", "error"] = "running"
    modules: dict[str, ModuleResult] = {}
