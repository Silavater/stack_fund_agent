"""Authoritative market state — part of the L4 input (AuthoritativeState)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketState:
    session: str = "closed"  # "open" | "closed" | "pre" | "post"
    as_of: str = ""
