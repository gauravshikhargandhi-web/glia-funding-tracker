"""Collector for Madison Metropolitan Sewerage District (Madison, WI) bids and RFPs.

The District's Contracting Center is a WordPress section with an RSS feed of
its advertisements for bids and requests for proposals. The deadline is read
from the notice text ("Sealed bids will be accepted until 10:00 a.m., Tuesday,
October 27, 2026") when it is there. Many notices only point to QuestCDN for
the documents and give no date, so a notice without one counts for 45 days
after it was posted.
"""

import datetime
import email.utils
import html
import re

from tracker.text import clean, fetch

FEED_URL = "https://www.madsewer.org/contracting-center/feed/"
MAX_AGE_DAYS = 45

_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_DEADLINE = re.compile(
    rf"(?:accepted until|received by|received until|due|no later than|deadline)(?:[^.]|\b[ap]\.m\.){{0,60}}?"
    rf"\b({_MONTHS})\s+(\d{{1,2}}),?\s+(\d{{4}})", re.IGNORECASE)


def _text(fragment):
    fragment = re.sub(r"(?s)^<!\[CDATA\[(.*)\]\]>$", r"\1", fragment.strip())
    text = re.sub(r"\s+", " ", html.unescape(clean(fragment))).strip()
    return re.sub(r"\s*The post .* appeared first on Madison Metropolitan Sewerage District\s*\.?$", "", text)


def parse(feed):
    """One dict per notice in the feed."""
    items = re.findall(r"(?s)<item>(.*?)</item>", feed)
    if not items and "<rss" not in feed:
        raise ValueError("Madison MSD feed changed: no RSS items")
    notices = []
    for item in items:
        tag = lambda name: (re.search(rf"(?s)<{name}>(.*?)</{name}>", item) or [None, ""])[1]
        posted = ""
        try:
            posted = email.utils.parsedate_to_datetime(tag("pubDate").strip()).date().isoformat()
        except (TypeError, ValueError):
            pass
        notices.append({
            "title": _text(tag("title")),
            "link": _text(tag("link")),
            "posted": posted,
            "text": _text(tag("content:encoded") or tag("description")),
        })
    return notices


def _kind(title, text):
    words = f"{title} {text[:300]}".lower()
    if "request for information" in words or re.search(r"\brfi\b", words):
        return "Contract (request for information)"
    if "proposal" in words or re.search(r"\brfp\b|\brfq\b", words):
        return "Contract (RFP)"
    return "Contract (bid)"


def normalize(notice):
    found = _DEADLINE.search(notice["text"])
    close = ""
    if found:
        month, day, year = found.groups()
        close = datetime.datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date().isoformat()
    return {
        "source": "madsewer",
        "source_id": notice["link"].rstrip("/").rsplit("/", 1)[-1],
        "title": notice["title"],
        "funder": "Madison Metropolitan Sewerage District",
        "funder_code": "MMSD-Madison",
        "listing_type": _kind(notice["title"], notice["text"]),
        "status": "posted",
        "post_date": notice["posted"],
        "close_date": close,
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": "",
        "eligibility": "Any vendor",
        "topics": "",
        "location": "Madison, WI",
        "link": notice["link"],
        "summary": notice["text"],
    }


def collect(today, feed=None):
    """Return the District's open bids and RFPs in the common format.

    Pass feed (the RSS text) to skip the download, e.g. in tests.
    """
    if feed is None:
        feed = fetch(FEED_URL, timeout=60).decode("utf-8", "replace")
    oldest = (today - datetime.timedelta(days=MAX_AGE_DAYS)).isoformat()
    rows = []
    for notice in parse(feed):
        row = normalize(notice)
        if row["close_date"]:
            if row["close_date"] < today.isoformat():
                continue
        elif not row["post_date"] or row["post_date"] < oldest:
            continue
        rows.append(row)
    return rows
