"""Pluggable fundamentals provider seam."""

from __future__ import annotations

import pathlib

from stackfund.l1_databook import (
    FixtureFundamentals,
    FundamentalsProvider,
    SitcaFundamentals,
    load_databook,
)

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "fixtures"


def test_fixture_provider_returns_only_fundamental_fields():
    p = FixtureFundamentals({"yield": 8.5, "nav": 37.0, "price": 52.8, "volume_shares": 1})
    f = p.fundamentals("0056")
    assert f == {"yield": 8.5, "nav": 37.0}  # price/volume are NOT fundamentals
    assert p.name == "fixture"


def test_sitca_stub_returns_none():
    s = SitcaFundamentals()
    assert s.name == "sitca"
    assert s.fundamentals("0056") is None
    assert isinstance(s, FundamentalsProvider)


class _FakeLiveNav:
    name = "fake-live-nav"

    def fundamentals(self, symbol: str):
        return {"nav": 999.0, "yield": 12.3, "discount_premium": -1.5}


def test_seam_custom_provider_overrides_and_marks_live():
    db = load_databook("0056", live=False, fixtures_dir=FIXTURES, fundamentals=_FakeLiveNav())
    assert db.metrics["nav"] == 999.0
    assert db.metrics["yield"] == 12.3
    assert db.metrics["discount_premium"] == -1.5
    assert db.freshness == "live"  # a real fundamentals feed marks the book live


def test_default_provider_keeps_frozen():
    db = load_databook("0056", live=False, fixtures_dir=FIXTURES)
    assert db.freshness == "frozen"
    assert db.metrics["yield"] == 8.5  # unchanged fixture fundamentals
