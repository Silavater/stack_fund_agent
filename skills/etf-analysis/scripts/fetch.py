#!/usr/bin/env python3
"""Thin wrapper: build/refresh an ETF DataBook via the StackFund engine.

Completes the upstream tw-stock-agent fetch_twse.py / fetch_yahoo.py placeholders
(now real connectors in stackfund.l1_databook.sources). Pass --live to overlay
official TWSE daily price/volume; omit it for the frozen fixture.
"""

from __future__ import annotations

import subprocess
import sys

if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, "-m", "stackfund", "fetch", *sys.argv[1:]]))
