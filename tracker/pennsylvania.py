"""Collector for Pennsylvania eMarketplace solicitations (state agencies,
state universities and authorities). Public search, no login.

The search page is an ASP.NET form; its "Export Search Results" button returns
every open solicitation as CSV, so one form post gets them all. Each
solicitation's page is Solicitations.aspx?SID=<bid number>.
"""

import csv
import datetime
import html
import io
import re
import urllib.parse

from tracker.text import fetch

SEARCH_URL = "https://www.emarketplace.state.pa.us/Search.aspx"
DETAIL_URL = "https://www.emarketplace.state.pa.us/Solicitations.aspx?SID={id}"
FORM = "ctl00$MainBody$"

# Bid types, from the site's own glossary.
_KINDS = {
    "RFI": "Contract (request for information)",
    "RFP": "Contract (RFP)",
    "RFA": "Grant (request for applications)",
    "SFP": "Contract (RFP)",
}


def _date(text):
    """'11/20/2026 3:00:00 PM' -> '2026-11-20'; blank for none or the 9999 placeholder."""
    try:
        date = datetime.datetime.strptime((text or "").split()[0], "%m/%d/%Y").date()
    except (ValueError, IndexError):
        return ""
    return "" if date.year >= 9999 else date.isoformat()


def download():
    page = fetch(SEARCH_URL, timeout=60).decode("utf-8", "replace")
    form = {name: html.unescape(value) for name, value in
            re.findall(r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', page)}
    if "__VIEWSTATE" not in form:
        raise ValueError("Pennsylvania eMarketplace layout changed: no search form")
    # Each drop-down's first option means "all".
    for name in ("ddlAgency", "ddlCounty", "ddlTypes"):
        first = re.search(rf'(?s)<select name="{re.escape(FORM + name)}".*?<option[^>]*value="([^"]*)"', page)
        form[FORM + name] = first.group(1) if first else ""
    form.update({FORM + "ddlRows": "32767", FORM + "rdolAdTypes": "11", FORM + "rdoArch": "0",
                 FORM + "btnExport": "Export Search Results"})
    return fetch(SEARCH_URL, timeout=120, data=urllib.parse.urlencode(form).encode(), headers={
        "Content-Type": "application/x-www-form-urlencoded", "Referer": SEARCH_URL,
    }).decode("utf-8", "replace")


def normalize(row):
    bid_type = row.get("Bid Type", "").strip()
    number = row.get("Bid No", "").strip()
    return {
        "source": "pa-emarketplace",
        "source_id": number,
        "title": row.get("Title", "").strip(),
        "funder": row.get("Agency", "").strip(),
        "funder_code": "PA",
        "listing_type": _KINDS.get(bid_type, f"Contract ({bid_type})" if bid_type else "Contract (bid)"),
        "status": "posted",
        "post_date": _date(row.get("Bid Start Date")),
        "close_date": _date(row.get("Bid End Date")),
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": "",
        "eligibility": "Any vendor",
        "topics": "; ".join(p for p in (bid_type, row.get("County", "").strip()) if p),
        "location": "Pennsylvania",
        "link": DETAIL_URL.format(id=urllib.parse.quote(number)),
        "summary": re.sub(r"\s+", " ", row.get("Description", "")).strip(),
    }


def collect(today, csv_text=None):
    """Return open Pennsylvania solicitations in the common format.

    Pass csv_text (the exported CSV) to skip the download, e.g. in tests.
    """
    if csv_text is None:
        csv_text = download()
    reader = csv.DictReader(io.StringIO(csv_text))
    if "Bid No" not in (reader.fieldnames or []):
        raise ValueError("Pennsylvania eMarketplace export changed: no 'Bid No' column")
    rows = []
    for row in reader:
        item = normalize(row)
        if item["source_id"] and (not item["close_date"] or item["close_date"] >= today.isoformat()):
            rows.append(item)
    return rows
