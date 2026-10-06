"""Collector for Michigan EGLE (Department of Environment, Great Lakes, and Energy)
grant and loan programs, from the public funding database on michigan.gov.

These are standing programs rather than dated calls: most say in their
description when a round is open. Programs marked closed are skipped.
"""

import html
import json
import re
import urllib.parse

from tracker.text import clean, fetch

SEARCH_URL = "https://www.michigan.gov/egle/sxa/search/results/"
# Ids of the funding database on https://www.michigan.gov/egle/regulatory-assistance/grants-and-financing
QUERY = {
    "s": "{8ED82AA3-C579-40D8-BB16-AC13E8805521}",
    "itemid": "{BB0149B0-4C53-41D0-976B-249B1BECC038}",
    "v": "{2C369B9B-E886-4F69-A45A-C749E4187C4F}",
    "p": "500",
    "o": "Title,Ascending",
}
SOURCES = {"State", "Federal"}
TYPES = {"Grant", "Loan", "Rebate"}
STATUSES = {"Accepting", "Closed - permanent"}
CLOSED = re.compile(r"\b(closed|discontinued|not being accepted|no longer accepting)\b", re.IGNORECASE)


def parse(result):
    page = result.get("Html", "")
    link = re.search(r'class="content-title-link" href="([^"]+)"[^>]*>(.*?)</a>', page, re.S)
    if not link:
        return None
    tags_block = re.search(r'(?s)<div class="d-none">(.*?)</div>', page)
    tags = [t.strip() for t in tags_block.group(1).split("\n") if t.strip()] if tags_block else []
    body = re.search(r'(?s)</a></div>\s*<div>(.*?)</div>', page)
    return {
        "id": result.get("Id", ""),
        "title": html.unescape(clean(link.group(2))),
        "link": urllib.parse.urljoin("https://www.michigan.gov", html.unescape(link.group(1))),
        "summary": html.unescape(clean(body.group(1))) if body else "",
        "tags": tags,
    }


def normalize(item):
    tags = item["tags"]
    topics = [t.removeprefix("Topic - ") for t in tags if t.startswith("Topic - ")]
    kinds = [t for t in tags if t in TYPES]
    applicants = [t for t in tags[1:] if t not in SOURCES | TYPES | STATUSES and not t.startswith("Topic - ")]
    # "Other" means applicants beyond the listed groups, e.g. businesses.
    applicants = ["Others (see listing)" if a == "Other" else a for a in applicants]
    return {
        "source": "michigan-egle",
        "source_id": item["id"],
        "title": item["title"],
        "funder": "Michigan EGLE",
        "funder_code": "MI-EGLE",
        "listing_type": f"{kinds[0]} program" if kinds else "Program",
        "status": "posted" if "Accepting" in tags else "rolling program",
        "post_date": "",
        "close_date": "",
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": "",
        "eligibility": "; ".join(applicants),
        "topics": "; ".join(topics),
        "location": "Michigan",
        "link": item["link"],
        "summary": item["summary"][:600],
    }


def collect(today, data=None):
    """Return EGLE programs that are not closed, in the common format.

    Pass data (the search JSON) to skip the download, e.g. in tests.
    """
    if data is None:
        data = json.loads(fetch(SEARCH_URL + "?" + urllib.parse.urlencode(QUERY), timeout=120))
    rows = []
    for result in data.get("Results") or []:
        item = parse(result)
        if not item or "Closed - permanent" in item["tags"] or CLOSED.search(item["summary"]):
            continue
        rows.append(normalize(item))
    return rows
