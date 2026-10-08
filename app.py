"""TelScope — unified local-first OSINT dashboard (MIT).

Binds 127.0.0.1 only. No telemetry. See PRIVACY.md / TERMS.md.
"""
from __future__ import annotations

import asyncio
import csv
import io
import json
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel

from adapters import ALL_ADAPTERS
from core.bus import Bus
from core.normalize import parse_target
from core.orchestrator import Orchestrator
from core.schema import Job
from core.store import Store

REPO = Path(__file__).resolve().parent
store = Store(REPO / "telscope.db")
bus = Bus()
orch = Orchestrator(ALL_ADAPTERS, store, bus)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    for a in ALL_ADAPTERS:
        sh = getattr(a, "shutdown", None)
        if sh:
            try:
                await sh()
            except Exception:
                pass


app = FastAPI(title="TelScope", version="1.0.0", lifespan=lifespan)


# ---------------------------------------------------------------- UI
@app.get("/")
async def index():
    return FileResponse(REPO / "web" / "index.html")


# ---------------------------------------------------------------- consent
class ConsentReq(BaseModel):
    accepted: bool


@app.get("/api/consent")
async def get_consent():
    return {"accepted": store.consent_accepted() is not None}


@app.post("/api/consent")
async def post_consent(req: ConsentReq):
    if not req.accepted:
        raise HTTPException(400, "consent must be accepted to run sweeps")
    return {"accepted_at": store.accept_consent()}


# ---------------------------------------------------------------- health
@app.get("/api/health")
async def health():
    return await orch.health_all()


# ---------------------------------------------------------------- settings
@app.get("/api/settings")
async def get_settings():
    return store.get_settings()


@app.put("/api/settings")
async def put_settings(patch: dict):
    return store.put_settings(patch)


# ---------------------------------------------------------------- sweep
class SweepReq(BaseModel):
    raw: str
    modules: list[str] = []
    region: Optional[str] = None


@app.post("/api/sweep")
async def sweep(req: SweepReq):
    if store.consent_accepted() is None:
        raise HTTPException(403, "consent required before running sweeps")
    settings = store.get_settings()
    try:
        target = parse_target(req.raw, req.region or settings.get("region", "BD"))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    job = Job(target=target)
    modules = req.modules or orch.applicable(target.type)
    modules = [m for m in modules if m in orch.applicable(target.type)]
    if not modules:
        raise HTTPException(422, "no applicable modules for this target type")
    store.save_job(job)
    asyncio.create_task(orch.run_sweep(job, modules))
    return {"job_id": job.job_id, "applicable": orch.applicable(target.type)}


# ---------------------------------------------------------------- SSE
@app.get("/api/stream/{job_id}")
async def stream(job_id: str):
    q, replay = bus.subscribe(job_id)

    async def gen():
        try:
            for ev in replay:
                yield f"data: {json.dumps(ev)}\n\n"
            while True:
                ev = await q.get()
                yield f"data: {json.dumps(ev)}\n\n"
                if ev.get("ev") == "job_done":
                    break
        finally:
            bus.unsubscribe(job_id, q)

    return StreamingResponse(
        gen(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------- jobs
@app.get("/api/jobs")
async def jobs(limit: int = 50):
    return store.list_jobs(limit)


@app.get("/api/jobs/{job_id}")
async def job(job_id: str):
    j = store.get_job(job_id)
    if not j:
        raise HTTPException(404, "job not found")
    return j


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    store.delete_job(job_id)
    return {"ok": True}


@app.delete("/api/jobs")
async def clear_history():
    store.clear_history()
    return {"ok": True}


class ManualReq(BaseModel):
    module: str
    raw: str


@app.post("/api/jobs/{job_id}/manual")
async def manual(job_id: str, req: ManualReq):
    j = store.add_manual_raw(job_id, req.module, req.raw)
    if not j:
        raise HTTPException(404, "job not found")
    return j


# ---------------------------------------------------------------- export
def _report_html(job: Job) -> str:
    rows = []
    for name, res in job.modules.items():
        for f in res.findings:
            rows.append(
                f"<tr><td>{name}</td><td>{f.type}</td><td>{f.key}</td>"
                f"<td>{f.value}</td><td>{f.confidence}</td></tr>"
            )
    t = job.target
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>TelScope report {job.job_id}</title>
<style>
body{{font:14px/1.5 system-ui,Segoe UI,sans-serif;background:#0b1220;color:#e2e8f0;padding:32px}}
h1{{font-size:22px}} .muted{{color:#94a3b8}} table{{border-collapse:collapse;width:100%;margin-top:16px}}
td,th{{border:1px solid #1e293b;padding:7px 10px;text-align:left;font-size:13px}}
th{{color:#22d3ee}} .badge{{display:inline-block;border:1px solid #1e293b;border-radius:6px;padding:2px 8px;margin-right:6px}}
@media print{{body{{background:#fff;color:#000}} td,th{{border-color:#ccc}} th{{color:#0369a1}}}}
</style></head><body>
<h1>🔭 TelScope report</h1>
<p class="muted">job {job.job_id} · {time.ctime(job.created_at)} · target: <b>{t.raw}</b>
({t.type}{', ' + t.e164 if t.e164 else ''}) · status {job.status}</p>
<p>{''.join(f'<span class="badge">{n}: {r.status}</span>' for n, r in job.modules.items())}</p>
<table><tr><th>module</th><th>type</th><th>key</th><th>value</th><th>confidence</th></tr>
{''.join(rows) or '<tr><td colspan=5>no findings</td></tr>'}</table>
<p class="muted">Generated by TelScope (MIT) · outputs are leads, not proof · see TERMS.md</p>
</body></html>"""


@app.get("/api/jobs/{job_id}/export")
async def export(job_id: str, format: str = "json"):
    j = store.get_job(job_id)
    if not j:
        raise HTTPException(404, "job not found")
    if format == "json":
        return Response(
            json.dumps(j.model_dump(), indent=2), media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=telscope-{job_id}.json"})
    if format == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["job_id", "module", "status", "type", "key", "value", "confidence", "source"])
        for name, res in j.modules.items():
            for f in res.findings:
                w.writerow([job_id, name, res.status, f.type, f.key, f.value, f.confidence, f.source])
        return Response(
            buf.getvalue(), media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=telscope-{job_id}.csv"})
    if format == "html":
        return Response(
            _report_html(j), media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename=telscope-{job_id}.html"})
    raise HTTPException(422, "format must be json|csv|html")


if __name__ == "__main__":
    import os

    # Default: localhost-only (privacy design). TELSCOPE_HOST override exists for
    # reverse-proxied demos (e.g. cloud sandboxes); never ship a public bind.
    host = os.environ.get("TELSCOPE_HOST", "127.0.0.1")
    port = int(os.environ.get("TELSCOPE_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="warning")
