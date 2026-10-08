"""Local SQLite persistence: jobs, settings, consent (MIT). No telemetry."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

from .schema import Job, ModuleResult, Target

_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS consent(id INTEGER PRIMARY KEY CHECK (id=1), accepted_at REAL);
CREATE TABLE IF NOT EXISTS jobs(
  id TEXT PRIMARY KEY, created_at REAL, target_raw TEXT, target_type TEXT,
  status TEXT, result_json TEXT
);
"""

DEFAULT_SETTINGS = {
    "region": "BD",
    "concurrency": "3",
    "module_timeout": "120",
    "phoneinfoga_port": "5001",
    "numverify_key": "",
    "allow_bruteforce": "false",
}


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()
        with self._conn() as c:
            c.executescript(_SCHEMA)

    def _conn(self):
        return sqlite3.connect(self.path, timeout=10)

    # settings ---------------------------------------------------------
    def get_settings(self) -> dict:
        with self._lock, self._conn() as c:
            rows = dict(c.execute("SELECT key,value FROM settings").fetchall())
        out = dict(DEFAULT_SETTINGS)
        out.update(rows)
        return out

    def put_settings(self, patch: dict) -> dict:
        with self._lock, self._conn() as c:
            for k, v in patch.items():
                if k in DEFAULT_SETTINGS:
                    c.execute(
                        "INSERT INTO settings(key,value) VALUES(?,?) "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (k, str(v)),
                    )
        return self.get_settings()

    # consent ----------------------------------------------------------
    def consent_accepted(self) -> Optional[float]:
        with self._lock, self._conn() as c:
            row = c.execute("SELECT accepted_at FROM consent WHERE id=1").fetchone()
        return row[0] if row else None

    def accept_consent(self) -> float:
        ts = time.time()
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT INTO consent(id,accepted_at) VALUES(1,?) "
                "ON CONFLICT(id) DO UPDATE SET accepted_at=excluded.accepted_at",
                (ts,),
            )
        return ts

    # jobs -------------------------------------------------------------
    def save_job(self, job: Job) -> None:
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT INTO jobs(id,created_at,target_raw,target_type,status,result_json) "
                "VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                "status=excluded.status, result_json=excluded.result_json",
                (
                    job.job_id, job.created_at, job.target.raw,
                    job.target.type, job.status,
                    json.dumps(job.model_dump()),
                ),
            )

    def list_jobs(self, limit: int = 50) -> list[dict]:
        with self._lock, self._conn() as c:
            rows = c.execute(
                "SELECT result_json FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        out = []
        for (rj,) in rows:
            try:
                out.append(json.loads(rj))
            except json.JSONDecodeError:
                continue
        return out

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock, self._conn() as c:
            row = c.execute(
                "SELECT result_json FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
        if not row:
            return None
        try:
            return Job(**json.loads(row[0]))
        except Exception:
            return None

    def delete_job(self, job_id: str) -> None:
        with self._lock, self._conn() as c:
            c.execute("DELETE FROM jobs WHERE id=?", (job_id,))

    def clear_history(self) -> None:
        with self._lock, self._conn() as c:
            c.execute("DELETE FROM jobs")

    def add_manual_raw(self, job_id: str, module: str, raw: str) -> Optional[Job]:
        job = self.get_job(job_id)
        if not job:
            return None
        res = job.modules.get(module) or ModuleResult(module=module, status="manual")
        res.status = "manual"
        res.raw_log = raw
        res.warnings = [
            w for w in res.warnings if "Assisted manual" not in w
        ] + ["Raw output pasted by user (assisted manual mode)."]
        job.modules[module] = res
        self.save_job(job)
        return job
