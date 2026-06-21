"""Pluggable fundamentals provider for ETF yield / NAV / discount_premium /
tracking_error / catalyst_strength.

There is NO clean free JSON feed for these (verified 2026-06): TWSE OpenAPI
``BWIBBU_ALL`` excludes ETFs; Yahoo v7/v10 require a cookie+crumb (currently
region-gated); SITCA serves an ASP.NET ``__VIEWSTATE`` form. So the default
carries fundamentals from the data book's fixture, labelled *reference*. To make
them live, implement ``FundamentalsProvider`` against a stable feed and pass it
to ``load_databook(..., fundamentals=...)`` — that is the only change needed.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

# The fields a fundamentals provider may supply (everything price/volume/momentum
# is already live via the TWSE/Yahoo connectors and is NOT a fundamentals field).
FUNDAMENTAL_FIELDS = ("yield", "nav", "discount_premium", "tracking_error", "catalyst_strength")


@runtime_checkable
class FundamentalsProvider(Protocol):
    name: str

    def fundamentals(self, symbol: str) -> dict[str, float] | None:
        """Return a subset of FUNDAMENTAL_FIELDS for ``symbol``, or None to fall back."""
        ...


class FixtureFundamentals:
    """Default provider: carry fundamentals from the fixture metrics (reference)."""

    name = "fixture"

    def __init__(self, fixture_metrics: dict[str, float]) -> None:
        self._metrics = fixture_metrics

    def fundamentals(self, symbol: str) -> dict[str, float] | None:
        return {k: self._metrics[k] for k in FUNDAMENTAL_FIELDS if k in self._metrics}


class SitcaFundamentals:
    """STUB adapter for SITCA daily fund NAV (sitca.org.tw, IN2422).

    NOT wired by default — it is a documented seam, not a shipped scraper, so it
    cannot break a demo. A robust implementation must: (1) GET the page to capture
    ``__VIEWSTATE`` / ``__EVENTVALIDATION``; (2) POST the date + fund-type
    selection; (3) parse the returned HTML table for the fund's 淨值; (4) compute
    ``discount_premium = (price - nav) / nav * 100``. Until implemented it returns
    None, so callers gracefully fall back to the fixture.
    """

    name = "sitca"
    base_url = "https://www.sitca.org.tw/ROC/Industry/IN2422.aspx?PGMID=FF0301"

    def fundamentals(self, symbol: str) -> dict[str, float] | None:
        # TODO: implement the __VIEWSTATE POST + HTML-table parse against a stable
        # NAV feed. Intentionally unimplemented (returns None -> fixture fallback).
        return None
