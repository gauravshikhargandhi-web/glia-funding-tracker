"""Collector for federal prize challenges listed on USA.gov.

Challenge.gov's listings moved to USA.gov's "Browse active challenges" page:
a set of cards, each linking to a page with a description and a "Key
information" table (sponsoring agency, start and end dates, prizes).
"""

import datetime
import html
import re

from tracker.text import clean, fetch

BASE = "https://www.usa.gov"
PAGE_URL = BASE + "/find-active-challenge"

_CARD = re.compile(r'(?s)<a href="(/challenges/[^"]+)" class="usa-card__container.*?<h2[^>]*>(.*?)</h2>.*?<p>(.*?)</p>')
_ROW = re.compile(r"(?s)<tr><th>(.*?)</th><td>(.*?)</td></tr>")
_DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")


def _text(fragment):
    return re.sub(r"\s+", " ", html.unescape(clean(fragment))).strip()


def parse_list(page):
    """(path, title, teaser) for each active challenge."""
    cards = [(path, _text(title), _text(teaser)) for path, title, teaser in _CARD.findall(page)]
    if not cards:
        raise ValueError("USA.gov challenges page layout changed: no challenge cards found")
    return cards


def parse_detail(page):
    """The key-information table as {label: text}, the description, and the
    link to the agency's own competition page."""
    body = re.search(r'(?s)<div class="usa-prose body-copy">(.*?)</div>', page)
    body = body.group(1) if body else ""
    info = {_text(label).lower(): _text(value) for label, value in _ROW.findall(body)}
    description = _text(re.sub(r"(?s)<table.*?</table>", " ", body))
    button = re.search(r'<a class="usa-button[^"]*" href="([^"]+)"', body)
    return info, description, html.unescape(button.group(1)) if button else ""


def _date(text):
    found = _DATE.search(text or "")
    if not found:
        return ""
    month, day, year = (int(n) for n in found.groups())
    return datetime.date(year, month, day).isoformat()


def _prize(text):
    found = re.search(r"\$([\d,]+)", text or "")
    return found.group(1).replace(",", "") if found else ""


def normalize(path, title, teaser, info, description, agency_link):
    return {
        "source": "usa.gov-challenges",
        "source_id": path.rsplit("/", 1)[-1],
        "title": title,
        "funder": info.get("sponsoring agency", ""),
        "funder_code": "",
        "listing_type": "Prize",
        "status": "posted",
        "post_date": _date(info.get("start date")),
        "close_date": _date(info.get("end date")),
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": _prize(info.get("prizes")),
        "eligibility": "Others (see listing)",
        "topics": info.get("challenge type", ""),
        "location": "National",
        # The agency's own page has the rules and the entry form.
        "link": agency_link or BASE + path,
        "summary": " ".join(p for p in (teaser, description, info.get("prizes", "")) if p),
    }


def collect(today, page=None, details=None):
    """Return active federal challenges in the common format.

    Pass page (the list HTML) and details (path -> challenge page HTML) to skip
    the download, e.g. in tests.
    """
    if page is None:
        page = fetch(PAGE_URL, timeout=60).decode("utf-8", "replace")
    rows = []
    for path, title, teaser in parse_list(page):
        if details is not None:
            detail = details.get(path, "")
        else:
            try:
                detail = fetch(BASE + path, timeout=60).decode("utf-8", "replace")
            except Exception as exc:
                print(f"usa.gov challenges: could not read {path} ({exc})")
                detail = ""
        row = normalize(path, title, teaser, *parse_detail(detail))
        if not row["close_date"] or row["close_date"] >= today.isoformat():
            rows.append(row)
    return rows
