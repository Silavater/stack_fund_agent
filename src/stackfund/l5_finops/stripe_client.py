"""Real Stripe (TEST mode) client for L5 earn/spend — opt-in.

The key is read from a runtime secret (env ``STRIPE_SECRET_KEY``, env
``STRIPE_SECRET_KEY_FILE``, or ``secrets/stripe_secret_key.txt``); it is never
committed. SAFETY: this module **refuses any non-test key** (must start with
``sk_test_`` / ``rk_test_``) so it can never move real money. ``stripe`` is
imported lazily so the deterministic core never needs the SDK.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_DEFAULT_KEY_FILE = "secrets/stripe_secret_key.txt"

# Stripe zero-decimal currencies (amount is the whole unit, not cents).
_ZERO_DECIMAL = {
    "BIF", "CLP", "DJF", "GNF", "JPY", "KMF", "KRW", "MGA",
    "PYG", "RWF", "UGX", "VND", "VUV", "XAF", "XOF", "XPF",
}  # fmt: skip


def load_key() -> str | None:
    key = os.environ.get("STRIPE_SECRET_KEY")
    if not key:
        path = os.environ.get("STRIPE_SECRET_KEY_FILE")
        if not path:
            cand = Path(__file__).resolve().parents[3] / _DEFAULT_KEY_FILE
            path = str(cand) if cand.exists() else None
        if path and Path(path).exists():
            key = Path(path).read_text(encoding="utf-8")
    key = (key or "").strip()
    return key or None


def is_test_key(key: str) -> bool:
    return key.startswith(("sk_test_", "rk_test_"))


def is_configured() -> bool:
    key = load_key()
    return bool(key and is_test_key(key))


def to_minor_units(amount: float, currency: str) -> int:
    if currency.upper() in _ZERO_DECIMAL:
        return int(round(amount))
    return int(round(amount * 100))


def _client() -> Any:
    key = load_key()
    if not key:
        raise RuntimeError(
            "No Stripe key — set STRIPE_SECRET_KEY or write secrets/stripe_secret_key.txt"
        )
    if not is_test_key(key):
        raise RuntimeError(
            "REFUSING a non-test Stripe key — StackFund only uses sk_test_/rk_test_ (no real money)"
        )
    import stripe

    stripe.api_key = key
    return stripe


def verify_key() -> dict:
    """Cheap connectivity/permission check. Returns {livemode, ...}."""
    stripe = _client()
    bal = stripe.Balance.retrieve()
    return {"livemode": bal["livemode"], "object": bal["object"]}


def create_payment(
    amount: float, currency: str, description: str, payment_method: str = "pm_card_visa"
) -> dict:
    """Create + confirm a TEST-mode PaymentIntent. Returns {id, status, amount, currency}."""
    stripe = _client()
    pi = stripe.PaymentIntent.create(
        amount=to_minor_units(amount, currency),
        currency=currency.lower(),
        description=description,
        payment_method=payment_method,
        payment_method_types=["card"],
        confirm=True,
    )
    return {"id": pi.id, "status": pi.status, "amount": pi.amount, "currency": pi.currency}


def create_checkout_session(
    tier: str, amount: float, currency: str, success_url: str, cancel_url: str
) -> dict:
    """Create a TEST-mode Stripe Checkout Session (hosted page). Returns {id, url}.

    Uses inline ``price_data`` so no dashboard Price object is needed. The
    ``_client()`` guard means a live key can never create a real session.
    """
    stripe = _client()
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": to_minor_units(amount, currency),
                    "product_data": {"name": f"StackFund {tier} (test mode)"},
                },
            }
        ],
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return {"id": session.id, "url": session.url}


def retrieve_checkout_session(session_id: str) -> dict:
    """Server-side verify a Checkout Session. Returns {id, paid, amount, currency}."""
    stripe = _client()
    s = stripe.checkout.Session.retrieve(session_id)
    return {
        "id": s["id"],
        "paid": s["payment_status"] == "paid",
        "amount": (s["amount_total"] or 0) / 100.0,
        "currency": (s["currency"] or "").upper(),
    }
