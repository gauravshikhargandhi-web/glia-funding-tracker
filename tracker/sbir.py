"""Collector for SBIR.gov's topic search: every agency's open and upcoming
SBIR/STTR research topics (Defense, Energy, NSF, NASA and others).

SBIR.gov's data API refuses automated requests, but its public topic search
(www.sbir.gov/topics) has a Download button that returns every open topic as
one CSV. That is used rather than the result pages, whose order changes from
one request to the next, so paging through them skips and repeats topics.
Most Defense topics reach us only this way. Topics are kept when they match
the water keywords like any other listing.
"""

import csv
import datetime
import html
import io
import re
import urllib.parse

from tracker.text import clean, fetch

BASE = "https://www.sbir.gov"
SEARCH_URL = BASE + "/topics?status=1&page=0"
# The download is checked against the result count the search page shows; a
# much shorter file means something went wrong, so the source fails for the
# day (and keeps yesterday's topics) instead of dropping topics.
MIN_SHARE = 0.9
AGENCIES = {
    "DOD": "Department of Defense", "DOE": "Department of Energy", "NSF": "National Science Foundation",
    "NASA": "NASA", "HHS": "Department of Health and Human Services", "USDA": "Department of Agriculture",
    "EPA": "Environmental Protection Agency", "DHS": "Department of Homeland Security",
    "DOC": "Department of Commerce", "DOT": "Department of Transportation", "ED": "Department of Education",
}
# Agencies that award SBIR/STTR as grants; the rest (Defense, NASA, EPA, ...) award contracts.
GRANT_AGENCIES = {"NSF", "DOE", "USDA", "HHS"}


def _date(text):
    try:
        return datetime.datetime.strptime(text, "%B %d, %Y").date().isoformat()
    except ValueError:
        return ""


def normalize(topic, today):
    """One row of the downloaded CSV in the common format."""
    code = topic.get("Agency", "").strip()
    dates = {label: _date(topic.get(label, "").strip()) for label in ("Release Date", "Open Date", "Close Date")}
    not_open_yet = dates["Open Date"] and dates["Open Date"] > today.isoformat()
    program = topic.get("Program", "").strip()
    programs = "SBIR / STTR" if program == "BOTH" else (program or "SBIR")
    link = topic.get("SBIRTopicLink", "").strip()
    return {
        "source": "sbir.gov",
        "source_id": link.rstrip("/").rsplit("/", 1)[-1],
        "title": html.unescape(clean(topic.get("Topic Title", ""))),
        "funder": AGENCIES.get(code, code),
        "funder_code": code,
        "listing_type": ("Grant" if code in GRANT_AGENCIES else "Contract") + f" ({programs} topic)",
        "status": "forecast" if not_open_yet else "posted",
        "post_date": dates["Release Date"],
        "close_date": dates["Close Date"],
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": "",
        "eligibility": "Small businesses",
        "topics": "; ".join(["SBIR/STTR"] + ([f"Opens {dates['Open Date']}"] if not_open_yet else [])),
        "location": "National",
        "link": link,
        "summary": html.unescape(clean(topic.get("Topic Description", ""))),
    }


def collect(today, csv_text=None, expected=None):
    """Return open and upcoming SBIR/STTR topics in the common format.

    Pass csv_text (the downloaded CSV) and optionally expected (the result count
    the search page shows) to skip the download, e.g. in tests.
    """
    if csv_text is None:
        csv_text, expected = download()
    reader = csv.DictReader(io.StringIO(csv_text))
    if "SBIRTopicLink" not in (reader.fieldnames or []):
        raise ValueError("SBIR.gov download changed: no SBIRTopicLink column")
    topics = list(reader)
    if expected and len(topics) < expected * MIN_SHARE:
        raise ValueError(f"SBIR.gov download has {len(topics)} topics but the search shows {expected}")
    seen, rows = set(), []
    for topic in topics:
        row = normalize(topic, today)
        if not row["source_id"] or row["source_id"] in seen:
            continue
        seen.add(row["source_id"])
        if row["close_date"] and row["close_date"] < today.isoformat():
            continue
        rows.append(row)
    return rows


def download():
    """(CSV text, result count shown on the search page). The Download button
    posts the search form back with op=Download."""
    page = fetch(SEARCH_URL, timeout=60).decode("utf-8", errors="replace")
    count = re.search(r"of\s+([\d,]+)\s+results", page)
    form = page[page.find('<form class="topics-search'):]
    form = form[:form.find("</form>")]
    if not form:
        raise ValueError("SBIR.gov page layout changed: no search form")
    fields = {}
    for tag in re.findall(r"<input[^>]*>", form):
        name = re.search(r'name="([^"]+)"', tag)
        kind = re.search(r'type="([^"]+)"', tag)
        kind = kind.group(1) if kind else "text"
        if not name or kind == "submit" or (kind in ("checkbox", "radio") and "checked" not in tag):
            continue
        value = re.search(r'value="([^"]*)"', tag)
        fields[name.group(1)] = html.unescape(value.group(1)) if value else ""
    fields["op"] = "Download"
    text = fetch(SEARCH_URL, timeout=180, data=urllib.parse.urlencode(fields).encode(), headers={
        "Content-Type": "application/x-www-form-urlencoded", "Referer": SEARCH_URL,
    }).decode("utf-8", errors="replace")
    return text, int(count.group(1).replace(",", "")) if count else None
