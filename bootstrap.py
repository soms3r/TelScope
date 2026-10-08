"""TelScope bootstrap — pinned provisioning of third-party tools (MIT code).

Downloads/clones happen ON THE USER'S MACHINE from official sources at setup
time. Nothing third-party is redistributed in the release zip (see
THIRD-PARTY-NOTICES.md). Never raises: failures degrade to warnings and the
matching adapter reports `unavailable`.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent
BIN = REPO / "bin"
VENDOR = REPO / "vendor"
MARKER = REPO / ".bootstrap.json"

PHONEINFOGA_VERSION = "v2.11.0"
RELEASE_BASE = f"https://github.com/sundowndev/phoneinfoga/releases/download/{PHONEINFOGA_VERSION}"
PINS = {
    "email2phonenumber": ("https://github.com/martinvigo/email2phonenumber",
                          "9df9dbe838d4e32208b358df6de299474ff22a7d"),
    "X-osint": ("https://github.com/TermuxHackz/X-osint",
                "3c68bd8cecda4bc7865ea0dfbd6d55458aabaffe"),
    "Gokboru_Intel": ("https://github.com/AzizKpln/Gokboru_Intel",
                      "571a78fb59ca4b437e0daedebe90d4926e428ba9"),
}


def _asset_name() -> str:
    sysname, machine = platform.system(), platform.machine().lower()
    if sysname == "Linux":
        return "Linux_x86_64" if machine in ("x86_64", "amd64") else "Linux_arm64"
    if sysname == "Darwin":
        return "Darwin_arm64" if machine == "arm64" else "Darwin_x86_64"
    if sysname == "Windows":
        return "Windows_x86_64"
    return ""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _get(url: str, dest: Path) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
        return True
    except Exception as exc:
        print(f"[!] download failed {url}: {exc}")
        return False


def provision_phoneinfoga() -> str:
    asset = _asset_name()
    if not asset:
        return "unsupported platform — place binary in bin/ manually"
    exe = "phoneinfoga.exe" if platform.system() == "Windows" else "phoneinfoga"
    target = BIN / exe
    if target.exists():
        return f"already present: {target}"
    BIN.mkdir(parents=True, exist_ok=True)
    tar = BIN / f"phoneinfoga_{asset}.tar.gz"
    if not _get(f"{RELEASE_BASE}/phoneinfoga_{asset}.tar.gz", tar):
        return "download failed (offline?) — adapter will stay unavailable"
    sums = BIN / "phoneinfoga_checksums.txt"
    ok = False
    if _get(f"{RELEASE_BASE}/phoneinfoga_checksums.txt", sums):
        want = None
        for line in sums.read_text().splitlines():
            if f"phoneinfoga_{asset}.tar.gz" in line:
                want = line.split()[0]
        ok = want is not None and _sha256(tar) == want
        if not ok:
            tar.unlink(missing_ok=True)
            return "checksum mismatch — aborting download"
    else:
        tar.unlink(missing_ok=True)
        return "checksums unavailable — aborting download"
    shutil.unpack_archive(tar, BIN)
    tar.unlink(missing_ok=True)
    os.chmod(target, 0o755)
    return f"installed {PHONEINFOGA_VERSION} ({asset}, sha256-verified)"


def provision_vendor(name: str, url: str, commit: str) -> str:
    dest = VENDOR / name
    if (dest / ".git").exists() or any(dest.iterdir()) if dest.exists() else False:
        return f"already present: {dest}"
    if not shutil.which("git"):
        return "git not found — skipping vendor clone"
    VENDOR.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "clone", "--quiet", url, str(dest)],
                       capture_output=True, timeout=300)
    if r.returncode != 0:
        return f"clone failed: {r.stderr.decode(errors='replace')[:200]}"
    r2 = subprocess.run(["git", "checkout", "--quiet", commit], cwd=dest,
                        capture_output=True)
    return "cloned @ " + commit[:10] if r2.returncode == 0 else "cloned (checkout failed)"


def main() -> int:
    state = {}
    print("[*] TelScope bootstrap — pinned provisioning")
    state["phoneinfoga"] = provision_phoneinfoga()
    print("    phoneinfoga:", state["phoneinfoga"])
    for name, (url, commit) in PINS.items():
        state[name] = provision_vendor(name, url, commit)
        print(f"    {name}: {state[name]}")
    MARKER.write_text(json.dumps(state, indent=1))
    print("[*] bootstrap done. Missing pieces show as 'unavailable' in the UI — the app still runs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
