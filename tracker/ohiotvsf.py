"""Collector for Ohio Third Frontier's Technology Validation and Start-up Fund.

TVSF funds Ohio start-ups licensing technology from Ohio universities and
research institutes, in rounds a few times a year. Its page gives the current
round's timeline ("Round 46 - Phase 1 & 2 Timeline ... Proposals: Due by 4 p.m.
Aug. 6, 2026"). The round is listed while its proposal date is still ahead.
"""

import datetime
import html
import re

from tracker.text import clean, fetch

PAGE_URL = ("https://development.ohio.gov/business/third-frontier-and-technology/"
            "technology-validation-start-up-fund")

_MONTHS = {m[:3].lower(): i for i, m in enumerate(
    "January February March April May June July August September October November December".split(), 1)}
_ROUND = re.compile(r"Round (\d+)[^.]{0,40}?Timeline(.*?)(?:Evaluator|Press Releases|$)")
_DUE = re.compile(r"Proposals:\s*Due[^A-Za-z]*(?:by\s+[\d:]+\s*[ap]\.?m\.?\s*)?([A-Z][a-z]{2})[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})")


def _text(page):
    page = re.sub(r"(?s)<!--.*?-->", " ", page)
    page = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(clean(page))).strip()


def parse(page):
    """(round number, timeline text, proposal due date) for the round on the page."""
    text = _text(page)
    found = _ROUND.search(text)
    if not found:
        raise ValueError("Ohio TVSF page layout changed: no round timeline")
    due = _DUE.search(found.group(2))
    date = ""
    if due and due.group(1).lower() in _MONTHS:
        date = datetime.date(int(due.group(3)), _MONTHS[due.group(1).lower()], int(due.group(2))).isoformat()
    about = re.search(r"The goal of the Ohio Third Frontier.*?\.", text)
    return found.group(1), found.group(2).strip(), date, about.group(0) if about else ""


def collect(today, page=None):
    """Return the open TVSF round, if any, in the common format.

    Pass page (the HTML) to skip the download, e.g. in tests.
    """
    if page is None:
        page = fetch(PAGE_URL, timeout=60).decode("utf-8", "replace")
    number, timeline, due, about = parse(page)
    if not due or due < today.isoformat():
        return []
    return [{
        "source": "ohio-tvsf",
        "source_id": f"round-{number}",
        "title": f"Ohio Third Frontier Technology Validation and Start-up Fund, Round {number}",
        "funder": "Ohio Department of Development (Third Frontier)",
        "funder_code": "OH",
        "listing_type": "Grant",
        "status": "posted",
        "post_date": "",
        "close_date": due,
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": "",
        "eligibility": "Others (see listing)",
        "topics": "Start-up fund",
        "location": "Ohio",
        "link": PAGE_URL,
        "summary": f"{about} Timeline: {timeline}".strip(),
    }]
