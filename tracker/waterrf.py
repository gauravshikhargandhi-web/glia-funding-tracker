"""Collector for the Water Research Foundation's open research RFPs.

WRF's "Available Grants" page lists each open RFP as a card: program, project
number and title, the research objectives, the "Apply by" date and the
funding. WRF projects are led by consultants, universities and utilities
together, and technology companies take part as contractors or partners.
"""

import datetime
import html
import re

from tracker.text import clean, fetch

BASE = "https://portal.waterrf.org/"
PAGE_URL = BASE + "outbound-grants"


def _text(fragment):
    return re.sub(r"\s+", " ", html.unescape(clean(fragment))).strip()


def parse(page):
    # The page shows the same cards twice (list and grid view); read the first view only.
    start = page.find('id="tab1-body"')
    end = page.find('id="tab2-body"', start)
    view = page[start:end] if start >= 0 and end > start else page
    cards = []
    for card in view.split('<div class="m360-slxg-grants-box')[1:]:
        title = re.search(r"(?s)<h2[^>]*>(.*?)</h2>", card)
        if not title:
            continue
        link = re.search(r'<a href="([^"]+)" class="card-overlay-link"', card)
        program = re.search(r'(?s)<span class="m360-slxg-small-font"[^>]*>(.*?)</span>', card)
        body = re.search(r'(?s)<div class="m360-slxg-grey-text">(.*?)<div class="m360-slxg-grey-bg', card)
        due = re.search(r"Apply by\s*</div>\s*<span>\s*<b>\s*(\d{1,2}/\d{1,2}/\d{4})", card)
        amount = re.search(r"USD\s*\$([\d,]+)", card)
        cards.append({
            "title": _text(title.group(1)),
            "link": html.unescape(link.group(1)) if link else "",
            "program": _text(program.group(1)) if program else "",
            "description": _text(body.group(1)) if body else "",
            "due": due.group(1) if due else "",
            "amount": amount.group(1).replace(",", "") if amount else "",
        })
    if not cards:
        raise ValueError("WRF page layout changed: no grant cards found")
    return cards


def normalize(card):
    number = re.match(r"(\d+)\s*-\s*", card["title"])
    close = ""
    if card["due"]:
        close = datetime.datetime.strptime(card["due"], "%m/%d/%Y").date().isoformat()
    link = card["link"]
    if link and not link.startswith("http"):
        link = BASE + link.lstrip("/")
    return {
        "source": "waterrf",
        "source_id": number.group(1) if number else card["title"][:60],
        "title": card["title"],
        "funder": "Water Research Foundation",
        "funder_code": "WRF",
        "listing_type": "Contract (research RFP)",
        "status": "posted",
        "post_date": "",
        "close_date": close,
        "award_floor": "",
        "award_ceiling": card["amount"],
        "total_funding": "",
        "eligibility": "Others (see listing)",
        "topics": card["program"],
        "location": "National",
        "link": link or PAGE_URL,
        "summary": card["description"],
    }


def collect(today, page=None):
    """Return WRF's open RFPs in the common format.

    Pass page (the HTML) to skip the download, e.g. in tests.
    """
    if page is None:
        page = fetch(PAGE_URL, timeout=60).decode("utf-8", "replace")
    rows = [normalize(c) for c in parse(page)]
    return [r for r in rows if not r["close_date"] or r["close_date"] >= today.isoformat()]
