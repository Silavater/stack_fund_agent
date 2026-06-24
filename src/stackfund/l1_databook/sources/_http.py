"""Minimal stdlib JSON-over-HTTPS helper (no third-party deps).

``fetch_json`` adds a graceful ``FetchError`` + an optional on-disk cache (fresh hits
skip the network; a stale cache is a fallback when a feed is flaky). The caching idea +
the ``FetchError`` shape are adapted, minimally, from ST / Chen YuShen's
``stock_agent.utils`` (MIT) — see ``NOTICE``. ST's concurrency/retry machinery is left
out on purpose: StackFund fetches a handful of ETFs, not a whole market.
"""

from __future__ import annotations

import hashlib
import json
import os
import ssl
import time
import urllib.request
from pathlib import Path
from typing import Any

USER_AGENT = "Mozilla/5.0 (StackFund research desk)"


class FetchError(RuntimeError):
    """A network or JSON fetch failed (raised by :func:`fetch_json`)."""


def _context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    # Some Taiwan government endpoints (e.g. openapi.twse.com.tw) serve certs
    # missing the Subject Key Identifier extension, which Python 3.13+ rejects
    # under VERIFY_X509_STRICT. Relax ONLY that pedantic flag — full chain +
    # hostname verification stays ON (this is not CERT_NONE).
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


def get_json(url: str, headers: dict[str, str], timeout: int) -> Any:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout, context=_context()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _cache_path(url: str) -> Path | None:
    base = os.environ.get("STACKFUND_HTTP_CACHE")
    if base is None:  # default cache dir is gitignored runtime state
        base = str(Path(__file__).resolve().parents[4] / ".hermes-data" / "http_cache")
    if not base:
        return None
    return Path(base) / (hashlib.sha256(url.encode("utf-8")).hexdigest() + ".json")


def fetch_json(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 15,
    cache_ttl: float | None = None,
) -> Any:
    """``get_json`` + a graceful ``FetchError`` + an optional on-disk cache.

    With ``cache_ttl`` set, a fresh cache hit is returned without a network call, and a
    *stale* cache is served as a fallback when the network fails — so repeated ``--live``
    runs are fast and survive a flaky feed. Raises :class:`FetchError` on an uncacheable
    failure. ``cache_ttl=None`` (the default) disables caching entirely.
    """
    headers = headers or {"User-Agent": USER_AGENT}
    cpath = _cache_path(url) if cache_ttl is not None else None
    if cpath is not None and cpath.exists():
        try:
            if (time.time() - cpath.stat().st_mtime) < cache_ttl:
                return json.loads(cpath.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    try:
        data = get_json(url, headers, timeout)
    except Exception as exc:  # noqa: BLE001
        if cpath is not None and cpath.exists():  # stale fallback on network failure
            try:
                return json.loads(cpath.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
        raise FetchError(f"{type(exc).__name__} fetching {url}: {exc}") from exc
    if cpath is not None:
        try:
            cpath.parent.mkdir(parents=True, exist_ok=True)
            cpath.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return data
