#!/usr/bin/env python3
"""Thin wrapper: delegate to the deterministic StackFund engine CLI.

Skills stay thin — they shell out to `python -m stackfund` rather than vendoring
engine code (the opposite of the tw-stock-agent placeholder anti-pattern).
"""

from __future__ import annotations

import subprocess
import sys

if __name__ == "__main__":
    raise SystemExit(
        subprocess.call([sys.executable, "-m", "stackfund", "pipeline", *sys.argv[1:]])
    )
