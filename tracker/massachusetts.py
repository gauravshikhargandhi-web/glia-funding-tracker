"""Collector for Massachusetts COMMBUYS open bids (state agencies, cities and
authorities; grants are posted here too). Public search, no login.

The open-bid search shows 25 rows a page, so we page through it the way the
site's own "next page" button does. Illinois BidBuy runs on the same platform
(Periscope BuySpeed), so tracker/bidbuy.py reuses this code with its own host.
"""

import datetime
import html
import re
import urllib.parse

from tracker.text import clean, fetch

HOST = "https://www.commbuys.com"
SEARCH_PATH = "/bso/view/search/external/advancedSearchBid.xhtml"
DETAIL_PATH = "/bso/external/bidDetail.sda?docId={id}&external=true&parentUrl=close"
TABLE = "bidSearchResultsForm:bidResultId"
PAGE_SIZE = 25
MAX_PAGES = 100  # safety stop: 2,500 bids

_ROW = re.compile(r'(?s)<tr data-ri="\d+"[^>]*>(.*?)</tr>')
_CELL = re.compile(r"(?s)<td[^>]*>(.*?)</td>")


def _date(text):
    """'10/21/2026 3:00 PM' -> '2026-10-21'."""
    try:
        return datetime.datetime.strptime(text.split()[0], "%m/%d/%Y").date().isoformat()
    except (ValueError, IndexError):
        return ""


def parse(page):
    rows = []
    for row in _ROW.findall(page):
        cells = [html.unescape(clean(c)) for c in _CELL.findall(row)]
        if len(cells) < 10:
            continue
        rows.append({"id": cells[0], "org": cells[2], "description": cells[6],
                     "opening": cells[7], "status": cells[9]})
    return rows


def normalize(row, host=HOST, source="commbuys", code="MA", location="Massachusetts"):
    grant = "grant" in row["description"].lower()
    return {
        "source": source,
        "source_id": row["id"],
        "title": row["description"],
        "funder": row["org"],
        "funder_code": code,
        "listing_type": "Grant" if grant else "Contract (bid)",
        "status": "posted",
        "post_date": "",
        "close_date": _date(row["opening"]),
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": "",
        "eligibility": "Any vendor",
        "topics": "",
        "location": location,
        "link": host + DETAIL_PATH.format(id=urllib.parse.quote(row["id"])),
        "summary": "",
    }


def download(host=HOST):
    search_url = host + SEARCH_PATH
    first = fetch(search_url + "?openBids=true", timeout=180).decode("utf-8", errors="replace")
    form = first[first.find('<form id="bidSearchResultsForm"'):]
    form = form[:form.find("</form>")]
    state = re.search(r'name="javax.faces.ViewState"[^>]*value="([^"]+)"', form).group(1)
    csrf = re.search(r'name="_csrf" value="([^"]+)"', form).group(1)
    total = int(re.search(r"rowCount:(\d+)", first).group(1))
    pages = [first]
    for start in range(PAGE_SIZE, min(total, PAGE_SIZE * MAX_PAGES), PAGE_SIZE):
        body = {
            "javax.faces.partial.ajax": "true", "javax.faces.source": TABLE,
            "javax.faces.partial.execute": TABLE, "javax.faces.partial.render": TABLE,
            TABLE: TABLE, TABLE + "_pagination": "true", TABLE + "_first": str(start),
            TABLE + "_rows": str(PAGE_SIZE), TABLE + "_skipChildren": "true",
            TABLE + "_encodeFeature": "true", "bidSearchResultsForm": "bidSearchResultsForm",
            "_csrf": csrf, "openBids": "true", "javax.faces.ViewState": state,
        }
        pages.append(fetch(search_url, timeout=120, data=urllib.parse.urlencode(body).encode(), headers={
            "Faces-Request": "partial/ajax", "X-Requested-With": "XMLHttpRequest",
            "Origin": host, "Referer": search_url + "?openBids=true",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }).decode("utf-8", errors="replace"))
    return pages


def collect(today, pages=None, **site):
    """Return open COMMBUYS bids in the common format.

    Pass pages (the result pages' HTML) to skip the download, e.g. in tests.
    Pass host, source, code and location to read another site on the same platform.
    """
    if pages is None:
        pages = download(site.get("host", HOST))
    seen, out = set(), []
    for page in pages:
        for row in parse(page):
            item = normalize(row, **site)
            if item["source_id"] in seen or (item["close_date"] and item["close_date"] < today.isoformat()):
                continue
            seen.add(item["source_id"])
            out.append(item)
    return out
