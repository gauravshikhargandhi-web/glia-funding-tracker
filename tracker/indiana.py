"""Collector for Indiana state bids (IDOA Current Business Opportunities).

One HTML table of open events: name, agency, event ID, a description and the
response due date. Each event's bid documents are a public zip file; that is
the listing's link, since the event name only links to the bidder sign-up page.
"""

import datetime
import html
import re

from tracker.text import clean, fetch

PAGE_URL = "https://www.in.gov/idoa/procurement/current-business-opportunities/"

_DUE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def _text(fragment):
    fragment = re.sub(r"(?i)<br\s*/?>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(clean(fragment))).strip()


def parse(page):
    """One dict per row of the events table."""
    table = re.search(r'(?s)<table id="events-table".*?</table>', page)
    if not table:
        raise ValueError("Indiana page layout changed: no events table")
    events = []
    for tr in re.findall(r"(?s)<tr>(.*?)</tr>", table.group(0)):
        cells = re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)
        if len(cells) < 5:
            continue
        name = re.search(r"(?is)<a[^>]*>(.*?)</a>", cells[0])
        docs = re.search(r'(?i)<a href="([^"]+\.zip)"', cells[0])
        events.append({
            "name": _text(name.group(1) if name else cells[0]),
            "docs": docs.group(1) if docs else "",
            "agency": _text(cells[1]),
            "id": _text(cells[2]),
            "description": _text(cells[3]),
            "due": _text(cells[4]),
        })
    return events


def _kind(event):
    text = f"{event['name']} {event['description']}".lower()
    if "request for information" in text or re.search(r"\brfi\b", text):
        return "Contract (request for information)"
    if re.search(r"\brfp\b|request for proposal", text):
        return "Contract (RFP)"
    return "Contract (bid)"


def normalize(event):
    due = _DUE.search(event["due"])
    close = datetime.date(int(due.group(3)), int(due.group(1)), int(due.group(2))).isoformat() if due else ""
    link = event["docs"]
    if link.startswith("/"):
        link = "https://www.in.gov" + link
    return {
        "source": "indiana",
        "source_id": event["id"],
        "title": event["name"],
        "funder": f"State of Indiana - {event['agency']}" if event["agency"] else "State of Indiana",
        "funder_code": "IN",
        "listing_type": _kind(event),
        "status": "posted",
        "post_date": "",
        "close_date": close,
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": "",
        "eligibility": "Any vendor",
        "topics": event["agency"],
        "location": "Indiana",
        "link": link or PAGE_URL,
        "summary": event["description"],
    }


def collect(today, page=None):
    """Return open Indiana state bids in the common format.

    Pass page (the HTML) to skip the download, e.g. in tests.
    """
    if page is None:
        page = fetch(PAGE_URL, timeout=60).decode("utf-8", "replace")
    rows = [normalize(e) for e in parse(page)]
    return [r for r in rows if not r["close_date"] or r["close_date"] >= today.isoformat()]
