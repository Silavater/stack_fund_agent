"""Minimal stdlib JSON-over-HTTPS helper (no third-party deps)."""

from __future__ import annotations

import json
import ssl
import urllib.request
from typing import Any


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
