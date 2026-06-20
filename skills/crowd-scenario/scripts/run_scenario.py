#!/usr/bin/env python3
"""Thin wrapper: delegate to the deterministic StackFund crowd engine CLI.

Defaults to --dry-run (zero LLM, zero spend) so it is safe in CI and as a demo
fallback. The deterministic modifier is computed in Python regardless.
"""

from __future__ import annotations

import subprocess
import sys

if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, "-m", "stackfund", "crowd", *sys.argv[1:]]))
