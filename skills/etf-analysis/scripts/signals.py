#!/usr/bin/env python3
"""Thin wrapper: live Taiwan market context — chips (institutional net-buy via
TWSE T86, margin via MI_MARGN) + recent news headlines — for one symbol.

Context ONLY: these signals never enter the deterministic decision path (the
scorecard reads the DataBook, not this). Graceful: on any fetch failure the
engine prints what it has and moves on — safe to call in a live demo.
"""

from __future__ import annotations

import subprocess
import sys

if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, "-m", "stackfund", "signals", *sys.argv[1:]]))
