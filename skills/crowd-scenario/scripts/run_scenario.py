#!/usr/bin/env python3
"""Thin wrapper: delegate to the deterministic StackFund crowd engine CLI.

Defaults to --dry-run (zero LLM, zero spend) so it is safe in CI and as a demo
fallback. The categorical crowd_consensus is seed-derived in Python regardless —
there is NO numeric modifier (the artifact is narrative-only, non-authoritative).
"""

from __future__ import annotations

import subprocess
import sys

if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, "-m", "stackfund", "crowd", *sys.argv[1:]]))
