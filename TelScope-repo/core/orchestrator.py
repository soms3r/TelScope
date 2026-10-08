"""Concurrent sweep orchestrator (MIT): semaphore, timeouts, graceful degradation."""
from __future__ import annotations

import asyncio
import time

from adapters.base import Ctx
from core.bus import Bus
from core.schema import Job, ModuleResult
from core.store import Store


class Orchestrator:
    def __init__(self, adapters, store: Store, bus: Bus):
        self.adapters = {a.name: a for a in adapters}
        self.order = [a.name for a in adapters]
        self.store = store
        self.bus = bus

    def applicable(self, target_type: str) -> list[str]:
        return [n for n in self.order if target_type in self.adapters[n].inputs]

    async def health_all(self) -> dict:
        async def one(name):
            a = self.adapters[name]
            try:
                return name, await asyncio.wait_for(a.health(), 8)
            except Exception as exc:
                return name, {"available": False, "detail": f"health probe failed: {exc}"}

        pairs = await asyncio.gather(*(one(n) for n in self.order))
        return dict(pairs)

    async def run_sweep(self, job: Job, modules: list[str]) -> None:
        settings = self.store.get_settings()
        cap = max(1, int(settings.get("concurrency", 3)))
        hard = int(settings.get("module_timeout", 120)) + 60
        sem = asyncio.Semaphore(cap)
        selected = [
            self.adapters[m]
            for m in modules
            if m in self.adapters and job.target.type in self.adapters[m].inputs
        ]

        async def one(a) -> None:
            self.bus.publish(job.job_id, {
                "ev": "module_status", "module": a.name, "status": "running"})
            t0 = time.time()
            ctx = Ctx(
                settings,
                lambda line: self.bus.publish(job.job_id, {
                    "ev": "log", "module": a.name, "line": line}),
            )
            try:
                async with sem:
                    res = await asyncio.wait_for(a.run(job.target, ctx),
                                                 min(a.timeout_s + 30, hard))
            except asyncio.TimeoutError:
                res = ModuleResult(module=a.name, status="timeout",
                                   warnings=["module exceeded its timeout"])
            except Exception as exc:
                res = ModuleResult(module=a.name, status="error",
                                   warnings=[f"{type(exc).__name__}: {exc}"])
            res.duration_s = round(time.time() - t0, 1)
            job.modules[a.name] = res
            self.store.save_job(job)
            self.bus.publish(job.job_id, {
                "ev": "module_done", "module": a.name, "result": res.model_dump()})

        await asyncio.gather(*(one(a) for a in selected))
        job.status = "done"
        self.store.save_job(job)
        self.bus.publish(job.job_id, {"ev": "job_done", "job": job.model_dump()})
