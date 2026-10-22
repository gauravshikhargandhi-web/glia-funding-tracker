"""Collector for the Massachusetts Clean Energy Center's open funding programs.

The funding page lists open programs as cards (title, type, award and
deadlines), 12 to a page. Each program's own page has the full description,
which is read for keyword matching. Deadlines are free text ("Rolling",
"First Deadline: December 11, 2026 ..."), so the first date still ahead is used.
"""

import datetime
import html
import re

from tracker.text import clean, fetch

BASE = "https://www.masscec.com"
LIST_URL = BASE + "/funding?status%5Bopen%5D=open&page={page}"
MAX_PAGES = 5

_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_DATE = re.compile(rf"\b({_MONTHS})\s+(\d{{1,2}}),?\s+(\d{{4}})")


def _text(fragment):
    return re.sub(r"\s+", " ", html.unescape(clean(fragment))).strip()


def _field(card, name):
    found = re.search(rf'(?s)views-field-field-{name}">.*?<div class="field-content[^"]*">(.*?)</div>', card)
    return _text(found.group(1)) if found else ""


def parse_list(page):
    """The program cards on one page of the funding list."""
    cards = []
    for card in page.split('<div class="views-row">')[1:]:
        link = re.search(r'(?s)<a href="([^"]+)"[^>]*>(.*?)</a>', card)
        if not link:
            continue
        cards.append({
            "path": link.group(1),
            "title": _text(link.group(2)),
            "status": _field(card, "program-status"),
            "type": _field(card, "funding-type"),
            "award": _field(card, "award-limit"),
            "deadline": _field(card, "application-deadline"),
        })
    return cards


def parse_detail(page):
    """The description on a program's own page."""
    found = re.search(r'(?s)field--name-amino-content.*?>(.*?)<div[^>]*field--name-field-funding-op', page)
    return _text(found.group(1)) if found else ""


def close_date(deadline, today):
    """The first deadline still ahead; "" when there is none (rolling or not given),
    "closed" when every date given has passed."""
    dates = []
    for month, day, year in _DATE.findall(deadline):
        dates.append(datetime.datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date())
    ahead = sorted(d for d in dates if d >= today)
    if ahead:
        return ahead[0].isoformat()
    if dates and "rolling" not in deadline.lower():
        return "closed"
    return ""


def normalize(card, description, today):
    kind = card["type"] if card["type"] not in ("", "None") else "Program"
    award = "" if card["award"] in ("", "None") else card["award"]
    deadline = "" if card["deadline"] == "None" else card["deadline"]
    summary = " ".join(p for p in (
        f"Award: {award}." if award else "",
        f"Deadline: {deadline}." if deadline else "",
        description,
    ) if p)
    return {
        "source": "masscec",
        "source_id": card["path"].rstrip("/").rsplit("/", 1)[-1],
        "title": card["title"],
        "funder": "Massachusetts Clean Energy Center",
        "funder_code": "MassCEC",
        # "Grants", "Investments", "No-Cost Services", "Consulting/Services", ...
        "listing_type": kind,
        "status": "posted",
        "post_date": "",
        "close_date": close_date(deadline, today),
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": "",
        "eligibility": "Others (see listing)",
        "topics": kind,
        "location": "Massachusetts",
        "link": BASE + card["path"],
        "summary": summary,
    }


def collect(today, pages=None, details=None):
    """Return MassCEC's open programs in the common format.

    Pass pages (list HTML) and details (path -> program page HTML) to skip the
    download, e.g. in tests.
    """
    if pages is None:
        pages = []
        for n in range(MAX_PAGES):
            pages.append(fetch(LIST_URL.format(page=n), timeout=60).decode("utf-8", "replace"))
            if not parse_list(pages[-1]):
                break
    cards = [c for page in pages for c in parse_list(page) if c["status"].lower() == "open"]
    if pages and not cards:
        raise ValueError("MassCEC funding page layout changed: no open program cards found")
    rows = []
    for card in cards:
        if details is not None:
            detail = details.get(card["path"], "")
        else:
            try:
                detail = fetch(BASE + card["path"], timeout=60).decode("utf-8", "replace")
            except Exception as exc:
                # One missing program page shouldn't cost the whole source; the card still lists it.
                print(f"masscec: could not read {card['path']} ({exc})")
                detail = ""
        row = normalize(card, parse_detail(detail), today)
        if row["close_date"] != "closed":
            rows.append(row)
    return rows
