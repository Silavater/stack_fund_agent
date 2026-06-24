"""Google News RSS connector — recent Taiwan headlines for an ETF (catalyst context).

Adapted from ST / Chen YuShen's ``stock_agent.providers.news`` (MIT) — see ``NOTICE``.
Returns plain dicts. News is **catalyst context, never a decision input** — and it is
graceful (returns ``[]`` on any failure) so it can never break a research run.
"""

from __future__ import annotations

import email.utils
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC

from stackfund.l1_databook.sources._http import USER_AGENT

_BASE = "https://news.google.com/rss/search"


def fetch_news(symbol: str, limit: int = 3, timeout: int = 10) -> list[dict]:
    """Recent Taiwan-news headlines for an ETF symbol. ``[]`` on any failure."""
    params = urllib.parse.urlencode(
        {"q": f"{symbol} ETF 股票", "hl": "zh-TW", "gl": "TW", "ceid": "TW:zh-Hant"}
    )
    url = f"{_BASE}?{params}"
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, text/xml"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            root = ET.fromstring(response.read())
    except (OSError, TimeoutError, ET.ParseError):
        return []
    out = []
    for item in root.findall("./channel/item")[:limit]:
        out.append(
            {
                "title": _text(item, "title"),
                "publisher": _text(item, "source"),
                "published_at": _published(_text(item, "pubDate")),
                "url": _text(item, "link"),
            }
        )
    return out


def _text(node: ET.Element, tag: str) -> str | None:
    found = node.find(tag)
    if found is None or found.text is None:
        return None
    return found.text.strip() or None


def _published(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat(timespec="seconds")
