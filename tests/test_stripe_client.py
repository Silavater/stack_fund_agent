"""Stripe client — offline safety/logic tests (no network, no key needed)."""

from __future__ import annotations

import pytest

from stackfund.l5_finops import stripe_client


def test_is_test_key():
    assert stripe_client.is_test_key("sk_test_abc")
    assert stripe_client.is_test_key("rk_test_abc")
    assert not stripe_client.is_test_key("sk_live_abc")
    assert not stripe_client.is_test_key("rk_live_abc")


def test_to_minor_units():
    assert stripe_client.to_minor_units(299.0, "twd") == 29900  # 2-decimal
    assert stripe_client.to_minor_units(299.0, "TWD") == 29900
    assert stripe_client.to_minor_units(1000, "jpy") == 1000  # zero-decimal


def test_load_key_from_env(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "rk_test_xyz")
    assert stripe_client.load_key() == "rk_test_xyz"
    assert stripe_client.is_configured() is True


def test_refuse_live_key(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_danger")
    assert stripe_client.is_configured() is False  # live key is not "configured"
    with pytest.raises(RuntimeError, match="non-test"):
        stripe_client._client()


def test_no_key_returns_none(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("STRIPE_SECRET_KEY_FILE", "/definitely/nonexistent/path")
    assert stripe_client.load_key() is None
    assert stripe_client.is_configured() is False
