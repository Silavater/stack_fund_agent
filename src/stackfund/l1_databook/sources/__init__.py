"""L1 live data connectors (completed from AZNitro/tw-stock-agent placeholders).

Each connector splits a pure ``parse_*`` function (no network — unit-testable
against checked-in samples) from a thin ``fetch_*`` wrapper (network). Live fetch
is OPT-IN: the deterministic core pipeline runs on frozen fixtures with zero
egress; only L1 ingest reaches out, and only when asked.
"""

from __future__ import annotations

from stackfund.l1_databook.sources import twse, yahoo

__all__ = ["twse", "yahoo"]
