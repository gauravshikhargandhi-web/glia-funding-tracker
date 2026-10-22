"""Collector for Ohio's H2Ohio grant finder.

The "Find a Grant" page carries its table as JSON inside the HTML: title, link,
type of projects, funds, managing agency, when to apply and keywords. Programs
whose "when to apply" says funding was awarded or to check back later are not
open and are left out. None give an exact deadline.
"""

import html
import json
import re

from tracker.text import clean, fetch

PAGE_URL = "https://h2.ohio.gov/wps/portal/gov/h2ohio/partner-with-us/find-a-grant/find-a-grant"

_NOT_OPEN = re.compile(r"\b(check back|has been awarded|recent funding has been awarded|closed)\b", re.IGNORECASE)


def _text(value):
    return re.sub(r"\s+", " ", html.unescape(clean(str(value or "")))).strip()


def parse(page):
    """One dict per program, keyed by the table's column names."""
    start = page.find("{&quot;data&quot;")
    if start < 0:
        raise ValueError("H2Ohio page layout changed: no grant table data")
    data, _ = json.JSONDecoder().raw_decode(html.unescape(page[start:]))
    rows = data.get("data") or []
    # Row 0 is column formats, row 1 the column names.
    names = rows[1] if len(rows) > 1 else []
    return [dict(zip(names, (_text(v) for v in row))) for row in rows[2:] if len(row) >= len(names) and row[0]]


def normalize(program):
    title = program.get("Title", "")
    return {
        "source": "h2ohio",
        "source_id": re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:80],
        "title": title,
        "funder": f"H2Ohio - {program.get('Managing Agency', '')}".rstrip(" -"),
        "funder_code": "OH",
        "listing_type": "Grant",
        "status": "posted",
        "post_date": "",
        "close_date": "",
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": "",
        "eligibility": "Others (see listing)",
        "topics": program.get("Keywords", ""),
        "location": "Ohio",
        "link": program.get("URL", "") or PAGE_URL,
        "summary": " ".join(p for p in (
            program.get("Type of Projects", ""),
            f"Funds: {program['Funds']}." if program.get("Funds") else "",
            f"When to apply: {program['When to Apply']}." if program.get("When to Apply") else "",
        ) if p),
    }


def collect(today, page=None):
    """Return the H2Ohio programs open now or on a rolling basis, in the common format.

    Pass page (the HTML) to skip the download, e.g. in tests.
    """
    if page is None:
        page = fetch(PAGE_URL, timeout=60).decode("utf-8", "replace")
    return [normalize(p) for p in parse(page) if not _NOT_OPEN.search(p.get("When to Apply", ""))]
