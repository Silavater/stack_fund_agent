"""Report Composer — reads the L6 authoritative snapshot + the crowd narrative
and assembles the Pro report. Archivable, but NEVER writes back to any decision
input. This is where crowd-vs-engine divergence is computed (L3 itself is
firewalled from the engine, so it cannot know the engine posture).
"""

from __future__ import annotations

from stackfund.report.composer import compose_divergence, engine_posture

__all__ = ["compose_divergence", "engine_posture"]
