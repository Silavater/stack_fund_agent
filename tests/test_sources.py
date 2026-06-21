"""Data-source connectors: parse real (checked-in) samples offline; live is gated."""

from __future__ import annotations

import json
import os
import pathlib

import pytest

from stackfund.l1_databook.sources import twse, yahoo

SAMPLES = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "samples"


def test_roc_date_to_iso():
    assert twse.roc_date_to_iso("1150618") == "2026-06-18"
    assert twse.roc_date_to_iso("") == ""


def test_parse_twse_stock_day_all():
    rows = json.loads((SAMPLES / "twse_stock_day_all.sample.json").read_text(encoding="utf-8"))
    q = twse.parse_stock_day_all(rows, "0050")
    assert q is not None
    assert q["close"] == 107.3
    assert q["volume_shares"] == 78557448
    assert q["observed_at"] == "2026-06-18"
    assert q["source"] == "TWSE:STOCK_DAY_ALL"


def test_parse_twse_missing_symbol_returns_none():
    rows = json.loads((SAMPLES / "twse_stock_day_all.sample.json").read_text(encoding="utf-8"))
    assert twse.parse_stock_day_all(rows, "9999") is None


def test_parse_yahoo_chart():
    payload = json.loads((SAMPLES / "yahoo_0050.sample.json").read_text(encoding="utf-8"))
    q = yahoo.parse_chart(payload, "0050")
    assert q is not None
    assert q["price"] == 107.3
    assert q["currency"] == "TWD"


def test_parse_yahoo_malformed_returns_none():
    assert yahoo.parse_chart({"chart": {"result": []}}, "0050") is None


def test_parse_yahoo_chart_series_5d_return():
    payload = json.loads((SAMPLES / "yahoo_0056_history.sample.json").read_text(encoding="utf-8"))
    s = yahoo.parse_chart_series(payload, "0056")
    assert s is not None
    assert s["n_closes"] == 24
    assert s["price_5d_return_pct"] == 6.473
    assert s["price"] == 52.8


def test_parse_yahoo_series_malformed_returns_none():
    assert yahoo.parse_chart_series({"chart": {"result": []}}, "0056") is None


@pytest.mark.skipif(
    os.environ.get("STACKFUND_LIVE") != "1",
    reason="live network test — set STACKFUND_LIVE=1 to run",
)
def test_live_twse_quote():
    q = twse.fetch_etf_quote("0050")
    assert q is not None
    assert q["close"] and q["close"] > 0


@pytest.mark.skipif(
    os.environ.get("STACKFUND_LIVE") != "1",
    reason="live network test — set STACKFUND_LIVE=1 to run",
)
def test_live_yahoo_history():
    s = yahoo.fetch_yahoo_history("0056")
    assert s is not None
    assert s["n_closes"] >= 6
    assert s["price_5d_return_pct"] is not None
