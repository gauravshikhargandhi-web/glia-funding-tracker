"""Collector for the DOE Water Power Technologies Office's funding table.

The office's funding page has one table of open opportunities: technology
area, type of funding, solicitation title (linked), open date and close date.
Most of its funding announcements also reach Grants.gov; this page adds the
technical-support programs (TEAMER, hydropower collaboration) that don't.
Fellowships are left out (kept by hand in the sheet).
"""

import datetime
import html
import re

from tracker.text import clean, fetch

PAGE_URL = "https://www.energy.gov/eere/water/funding-opportunities"

_DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")


def _text(fragment):
    return re.sub(r"\s+", " ", html.unescape(clean(fragment))).strip()


def parse(page):
    """(area, type, title, link, opens, closes) for each full row of the table.
    Rows that only continue the row above (rowspan) are skipped."""
    table = re.search(r"(?s)<table\b.*?</table>", page)
    if not table:
        raise ValueError("DOE Water Power page layout changed: no funding table")
    rows = []
    for tr in re.findall(r"(?s)<tr\b.*?</tr>", table.group(0)):
        cells = re.findall(r"(?s)<td\b[^>]*>(.*?)</td>", tr)
        if len(cells) < 5:
            continue
        link = re.search(r'href="([^"]+)"', cells[2])
        url = html.unescape(link.group(1)) if link else PAGE_URL
        if url.startswith("/"):
            url = "https://www.energy.gov" + url
        rows.append((_text(cells[0]), _text(cells[1]), _text(cells[2]), url, _text(cells[3]), _text(cells[4])))
    return rows


def _date(text):
    found = _DATE.search(text)
    if not found:
        return ""
    month, day, year = (int(n) for n in found.groups())
    return datetime.date(year, month, day).isoformat()


def normalize(area, kind, title, link, opens, closes):
    return {
        "source": "doe-water",
        "source_id": re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:80],
        "title": title,
        "funder": "DOE Water Power Technologies Office",
        "funder_code": "DOE",
        # "Technical Support", "Funding Opportunity Announcement", "Prize", ...
        "listing_type": kind,
        "status": "posted",
        "post_date": _date(opens),
        "close_date": _date(closes),
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": "",
        "eligibility": "Others (see listing)",
        "topics": area,
        "location": "National",
        "link": link,
        "summary": f"{area} {kind.lower()}. Opens: {opens}. Closes: {closes}.",
    }


def collect(today, page=None):
    """Return the open water power opportunities in the common format.

    Pass page (the funding page HTML) to skip the download, e.g. in tests.
    """
    if page is None:
        page = fetch(PAGE_URL, timeout=60).decode("utf-8", "replace")
    rows = []
    for row in parse(page):
        if "fellowship" in row[1].lower():
            continue
        listing = normalize(*row)
        if not listing["close_date"] or listing["close_date"] >= today.isoformat():
            rows.append(listing)
    return rows
