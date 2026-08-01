"""Resolve Rhubarb CLI path for lip-sync."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_CANDIDATES = (
    os.environ.get("RHUBARB_BIN"),
    "/opt/rhubarb/rhubarb",
    "/usr/local/bin/rhubarb",
    "rhubarb",
    str(ROOT / "tools" / "rhubarb" / "rhubarb"),
)


def rhubarb_bin() -> str:
    """Return path to rhubarb executable (env RHUBARB_BIN overrides)."""
    for c in _CANDIDATES:
        if not c:
            continue
        p = Path(c)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p.resolve())
        if "/" not in c and "\\" not in c:
            from shutil import which
            w = which(c)
            if w:
                return w
    return "rhubarb"


def rhubarb_available() -> bool:
    from shutil import which
    b = rhubarb_bin()
    if Path(b).is_file() and os.access(b, os.X_OK):
        return True
    return which(b) is not None
