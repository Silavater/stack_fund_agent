"""StackFund — Autonomous Taiwan ETF Research Desk (Hermes agent).

Core-B architecture:
  * ENGINE (deterministic Python trunk): L1 data book -> L2 scorecard -> L4
    portfolio manager -> L5 finops -> L6 audit. Computes every number.
  * FACE (non-authoritative narrative side-rail): L3 crowd scenario engine.
    Emits a narrative + a categorical, non-authoritative ``CrowdNarrative``
    (``crowd_consensus`` in {bearish, neutral, bullish}; no numeric scalar);
    it is structurally firewalled out of the decision path.

The firewall is enforced by `import-linter` contracts (see pyproject.toml) and
by the tests in tests/test_firewall_no_imports.py.
"""

__version__ = "0.1.0"
