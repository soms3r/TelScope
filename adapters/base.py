"""Adapter contract + process runners (MIT).

Separation doctrine: GPL-3.0 tools are ONLY executed as separate processes
(subprocess / pty / their own REST server). No GPL code is imported here.
"""
from __future__ import annotations

import asyncio
import os
import re
import shutil
import signal
import time
from pathlib import Path
from typing import Optional

from core.schema import ModuleResult, Target

REPO_ROOT = Path(__file__).resolve().parents[1]
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b[=>]|\r")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text).replace("\x1b[H\x1b[J", "")


# Set by app.py at startup: returns the current settings dict. Lets adapters
# whose health() takes no context (e.g. HIBP needs the API key) read settings.
settings_provider = None


def current_settings() -> dict:
    try:
        return settings_provider() if settings_provider else {}
    except Exception:
        return {}


class Ctx:
    """Per-run context handed to adapters."""

    def __init__(self, settings: dict, log):
        self.settings = settings
        self.log = log  # async-or-sync callable(line: str)


class Adapter:
    name: str = "base"
    inputs: set[str] = set()
    timeout_s: int = 120

    async def health(self) -> dict:
        return {"available": False, "detail": "not implemented"}

    async def run(self, target: Target, ctx: Ctx) -> ModuleResult:
        raise NotImplementedError


async def run_cmd(
    argv: list, timeout_s: int = 90, input_text: Optional[str] = None, cwd=None
) -> tuple[int, bytes]:
    """Run a command in its own process group; kill the group on timeout."""
    kwargs = dict(
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(cwd) if cwd else None,
        start_new_session=True,
    )
    kwargs["stdin"] = (
        asyncio.subprocess.PIPE if input_text is not None else asyncio.subprocess.DEVNULL
    )
    proc = await asyncio.create_subprocess_exec(*[str(a) for a in argv], **kwargs)
    try:
        out, _ = await asyncio.wait_for(
            proc.communicate(input_text.encode() if input_text else None), timeout_s
        )
    except asyncio.TimeoutError:
        _killpg(proc)
        raise
    return proc.returncode if proc.returncode is not None else -1, out or b""


def _killpg(proc) -> None:
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


async def run_pty(
    argv: list, input_text: str, timeout_s: int = 120, cwd=None, settle: float = 1.2
) -> tuple[int, bytes]:
    """Drive a TTY-hungry REPL through a pseudo-terminal (POSIX only)."""
    import select

    master, slave = os.openpty()
    proc = await asyncio.create_subprocess_exec(
        *[str(a) for a in argv],
        stdin=slave, stdout=slave, stderr=slave,
        cwd=str(cwd) if cwd else None, start_new_session=True,
    )
    os.close(slave)
    out = bytearray()

    def _reader() -> bytes:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                r, _, _ = select.select([master], [], [], 0.5)
            except (OSError, ValueError):
                break
            if r:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                out.extend(chunk)
            elif proc.returncode is not None:
                break
        return bytes(out)

    loop = asyncio.get_running_loop()
    reader_task = loop.run_in_executor(None, _reader)
    await asyncio.sleep(settle)
    try:
        os.write(master, input_text.encode())
    except OSError:
        pass
    try:
        data = await asyncio.wait_for(asyncio.wrap_future(reader_task), timeout_s + 10)
    except asyncio.TimeoutError:
        data = bytes(out)
    finally:
        if proc.returncode is None:
            _killpg(proc)
        try:
            os.close(master)
        except OSError:
            pass
    try:
        await asyncio.wait_for(proc.wait(), 5)
    except asyncio.TimeoutError:
        pass
    return proc.returncode if proc.returncode is not None else -1, data


def which_tool(names: list[str]) -> Optional[str]:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None
