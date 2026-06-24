"""Chips + news connectors — pure parsing (offline)."""

import xml.etree.ElementTree as ET

from stackfund.l1_databook.sources import chips, news  # import smoke
from stackfund.l1_databook.sources.twse import parse_int


def test_parse_int():
    assert parse_int("1,234,567") == 1234567
    assert parse_int("-500") == -500
    assert parse_int("N/A") is None
    assert parse_int(None) is None


def test_news_published_parses_rfc822():
    iso = news._published("Mon, 22 Jun 2026 09:30:00 GMT")
    assert iso is not None and iso.startswith("2026-06-22T09:30:00")
    assert news._published(None) is None
    assert news._published("not a date") is None


def test_news_text_extracts_and_trims():
    item = ET.fromstring("<item><title> Hello </title><empty></empty></item>")
    assert news._text(item, "title") == "Hello"
    assert news._text(item, "empty") is None
    assert news._text(item, "missing") is None


def test_chips_date_token():
    assert chips._date_token("2026-06-22") == "20260622"
    token = chips._date_token(None)  # default: a real trading day from the calendar
    assert len(token) == 8 and token.isdigit()
