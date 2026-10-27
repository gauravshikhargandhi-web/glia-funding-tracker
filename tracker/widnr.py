"""Collector for Wisconsin DNR water grant programs.

DNR's grants page is a catalog of about 80 programs with no open or closed
status; each program's own page gives its dates in plain text ("Pre-applications
are required and due September 15, 2026", "accepting Cycle A applications
through April 30, 2027"). The program pages to read are listed in profile.toml
under [wi_dnr]. A program is listed while a deadline on its page is still ahead.

These grants go to local governments, lake and sanitary districts, tribes and
nonprofits, so a startup takes part as a partner on someone else's application.
"""

import datetime
import html
import re

from tracker.text import clean, fetch

_MONTHS = {m[:3].lower(): i for i, m in enumerate(
    "January February March April May June July August September October November December".split(), 1)}
_DATE = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})"
# A date counts as a deadline when one of these comes shortly before it.
_DEADLINE = re.compile(r"(?:\bdue\b|\bdeadline|\bthrough\b|\buntil\b|\bby\b|[–-])[^.]{0,40}?" + _DATE, re.IGNORECASE)


def _text(page):
    page = re.sub(r"(?s)<(script|style|nav|header|footer)\b.*?</\1>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(clean(page))).strip()


def parse(page):
    """(title, text) of a program page."""
    title = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", page) or re.search(r"(?is)<title[^>]*>(.*?)</title>", page)
    name = _text(title.group(1)) if title else ""
    name = re.sub(r"\s*\|.*$", "", name)
    return name, _text(page)


def next_deadline(text, today):
    """The earliest deadline on the page that is today or later, or ""."""
    dates = []
    for month, day, year in (m.groups() for m in _DEADLINE.finditer(text)):
        try:
            date = datetime.date(int(year), _MONTHS[month[:3].lower()], int(day))
        except (KeyError, ValueError):
            continue
        if date >= today:
            dates.append(date)
    return min(dates).isoformat() if dates else ""


def normalize(link, name, text, close):
    return {
        "source": "wi-dnr",
        "source_id": link.rstrip("/").rsplit("/", 1)[-1].removesuffix(".html").lower(),
        "title": name,
        "funder": "Wisconsin Department of Natural Resources",
        "funder_code": "WI-DNR",
        "listing_type": "Grant",
        "status": "posted",
        "post_date": "",
        "close_date": close,
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": "",
        "eligibility": "Local governments; Tribes; Nonprofits (see listing)",
        "topics": "Water",
        "location": "Wisconsin",
        "link": link,
        "summary": text,
    }


def collect(today, programs=(), pages=None):
    """Return the listed DNR programs whose deadline is still ahead.

    programs is the list of program page links from profile.toml. Pass pages
    (link -> HTML) to skip the download, e.g. in tests.
    """
    rows = []
    for link in programs:
        page = pages.get(link, "") if pages is not None else fetch(link, timeout=60).decode("utf-8", "replace")
        name, text = parse(page)
        if not name:
            raise ValueError(f"Wisconsin DNR page layout changed: no title on {link}")
        close = next_deadline(text, today)
        if close:
            rows.append(normalize(link, name, text, close))
    return rows
