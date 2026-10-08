"""In-memory SSE event bus with replay buffer (MIT)."""
from __future__ import annotations

import asyncio
from typing import Any


class Bus:
    def __init__(self) -> None:
        self._subs: dict[str, list[asyncio.Queue]] = {}
        self._buf: dict[str, list[dict[str, Any]]] = {}

    def publish(self, job_id: str, ev: dict[str, Any]) -> None:
        buf = self._buf.setdefault(job_id, [])
        buf.append(ev)
        if len(buf) > 3000:
            self._buf[job_id] = buf[-2000:]
        for q in self._subs.get(job_id, []):
            q.put_nowait(ev)

    def subscribe(self, job_id: str) -> tuple[asyncio.Queue, list[dict[str, Any]]]:
        q: asyncio.Queue = asyncio.Queue()
        self._subs.setdefault(job_id, []).append(q)
        return q, list(self._buf.get(job_id, []))

    def unsubscribe(self, job_id: str, q: asyncio.Queue) -> None:
        subs = self._subs.get(job_id, [])
        if q in subs:
            subs.remove(q)
