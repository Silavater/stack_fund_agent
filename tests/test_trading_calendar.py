"""Trading-calendar logic — offline (empty temp holiday cache + env overrides)."""

from datetime import date, datetime

import pytest

from stackfund.l1_databook import trading_calendar as tc


@pytest.fixture(autouse=True)
def _empty_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("STACKFUND_HOLIDAY_CACHE_PATH", str(tmp_path / "holidays.json"))
    monkeypatch.delenv("STACKFUND_EXTRA_HOLIDAYS", raising=False)
    tc._reset_cache_for_tests()
    yield
    tc._reset_cache_for_tests()


def test_weekend_and_trading_day():
    assert tc.is_weekend(date(2026, 6, 20))  # Saturday
    assert not tc.is_weekend(date(2026, 6, 19))  # Friday
    assert tc.is_trading_day(date(2026, 6, 19))  # Friday, empty cache -> trading
    assert not tc.is_trading_day(date(2026, 6, 20))  # Saturday


def test_env_holiday_override(monkeypatch):
    monkeypatch.setenv("STACKFUND_EXTRA_HOLIDAYS", "2026-06-19")
    assert tc.is_taiwan_holiday(date(2026, 6, 19))
    assert not tc.is_trading_day(date(2026, 6, 19))  # now a (typhoon) closure


def test_previous_trading_day_skips_weekend():
    # From Sunday 2026-06-21, the previous trading day is Friday 2026-06-19.
    assert tc.previous_trading_day(date(2026, 6, 21)) == date(2026, 6, 19)
    assert tc.resolve_report_trading_day(date(2026, 6, 20)) == date(2026, 6, 19)  # Sat -> Fri


def test_holiday_payload_filters_resumption_markers():
    payload = [
        {"Date": "20260101", "Name": "中華民國開國紀念日", "Description": ""},
        {"Date": "20260105", "Name": "國曆新年開始交易日", "Description": ""},  # a trading day
    ]
    holidays = tc.parse_twse_holiday_payload(payload)
    assert "2026-01-01" in holidays
    assert "2026-01-05" not in holidays  # resumption marker filtered out


def test_session_phase():
    assert tc.trading_session_phase(datetime(2026, 6, 19, 10, 0, tzinfo=tc.TAIPEI)) == "open"
    assert tc.trading_session_phase(datetime(2026, 6, 19, 8, 0, tzinfo=tc.TAIPEI)) == "pre_open"
    assert (
        tc.trading_session_phase(datetime(2026, 6, 19, 13, 26, tzinfo=tc.TAIPEI)) == "close_auction"
    )
    assert tc.trading_session_phase(datetime(2026, 6, 19, 14, 0, tzinfo=tc.TAIPEI)) == "after_close"
    assert tc.trading_session_phase(datetime(2026, 6, 20, 10, 0, tzinfo=tc.TAIPEI)) == "closed_day"
