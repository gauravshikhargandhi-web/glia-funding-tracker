"""Collector for NYSERDA's research and development funding calls.

NYSERDA's full list of solicitations only renders in a browser, but its
Research & Development Funding page lists the current innovation calls
(PONs and RFIs) as plain links to their pages on the NYSERDA portal. Each
portal page gives the due date and a description.
"""

import datetime
import html
import re

from tracker.text import clean, fetch

PAGE_URL = "https://nyserda.ny.gov/All-Programs/Innovation-at-NYSERDA/Funding-Opportunities"

_ITEM = re.compile(r'(?s)<li>\s*<strong>\s*((?:PON|RFI|RFP|RFQL?)\s*\d+)\s*:?\s*</strong>\s*:?\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>')
_DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")


def _text(fragment):
    return re.sub(r"\s+", " ", html.unescape(clean(fragment))).strip()


def parse_page(page):
    """(number, link, title) for each call listed under Current Opportunities."""
    start = page.find("Current Opportunities")
    if start < 0:
        raise ValueError("NYSERDA page layout changed: no 'Current Opportunities' heading")
    calls = []
    for number, link, title in _ITEM.findall(page[start:page.find("</ul>", start)]):
        link = html.unescape(link)
        # Keep only the solicitation id; the rest is tracking.
        found = re.search(r"SolicitationId=([A-Za-z0-9]+)", link)
        if found:
            link = "https://portal.nyserda.ny.gov/CORE_Solicitation_Detail_Page?SolicitationId=" + found.group(1)
        calls.append((re.sub(r"\s+", " ", number), link, _text(title)))
    return calls


def parse_detail(page):
    """(due date text, description) from a portal page. The due date is
    "closed" when the portal says the solicitation has closed."""
    text = _text(re.sub(r"(?s)<(script|style)\b.*?</\1>", "", page))
    if "This solicitation is closed" in text:
        return ("closed", "")
    due = re.search(r"Due Date:\s*(.*?)\s*Description\b", text)
    description = re.search(r"\bDescription\s+(.*?)\s*(?:Application Submission|Associated Documents|Contact\b|$)", text)
    return (due.group(1) if due else "", description.group(1) if description else "")


def close_date(due, today):
    """The first due date still ahead; "" when none is given, "closed" when all have passed."""
    if due == "closed":
        return "closed"
    dates = [datetime.date(int(y), int(m), int(d)) for m, d, y in _DATE.findall(due)]
    ahead = sorted(d for d in dates if d >= today)
    if ahead:
        return ahead[0].isoformat()
    return "closed" if dates else ""


def normalize(number, link, title, due, description, today):
    rfi = number.startswith("RFI")
    return {
        "source": "nyserda",
        "source_id": number.replace(" ", "-"),
        "title": f"{title} ({number})",
        "funder": "NYSERDA",
        "funder_code": "NYSERDA",
        "listing_type": "Contract (request for information)" if rfi else "Grant (program opportunity notice)",
        "status": "posted",
        "post_date": "",
        "close_date": close_date(due, today),
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": "",
        "eligibility": "Others (see listing)",
        "topics": "Innovation and research",
        "location": "New York",
        "link": link,
        "summary": " ".join(p for p in (f"Due: {due}." if due else "", description) if p),
    }


def collect(today, page=None, details=None):
    """Return NYSERDA's current innovation calls in the common format.

    Pass page (the R&D funding page HTML) and details (link -> portal page HTML)
    to skip the download, e.g. in tests.
    """
    if page is None:
        page = fetch(PAGE_URL, timeout=60).decode("utf-8", "replace")
    rows = []
    for number, link, title in parse_page(page):
        if details is not None:
            detail = details.get(link, "")
        else:
            try:
                detail = fetch(link, timeout=60).decode("utf-8", "replace")
            except Exception as exc:
                # The page still lists the call; keep it without a due date.
                print(f"nyserda: could not read {number} ({exc})")
                detail = ""
        due, description = parse_detail(detail)
        row = normalize(number, link, title, due, description, today)
        if row["close_date"] != "closed":
            rows.append(row)
    return rows
