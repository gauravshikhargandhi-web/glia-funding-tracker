"""Collector for DOE's American-Made prizes, listed on HeroX.

American-Made runs most Department of Energy prize competitions; they are not
on Grants.gov. Its own site only renders in a browser, but its HeroX page lists
every challenge as a plain card with a stage ("Enter - 45 Days Remaining",
"Judging", "Won", ...) and the prize. Only challenges open for entries are kept.
"""

import datetime
import html
import re

from tracker.text import clean, fetch

BASE = "https://www.herox.com"
PAGE_URL = BASE + "/American-Made-Challenges"

_CARD = re.compile(r'(?s)<a href="(/[^"]+)" class="card-challenge">(.*?)</a>\s*</div>')


def _text(fragment):
    return re.sub(r"\s+", " ", html.unescape(clean(fragment))).strip()


def _part(card, name):
    found = re.search(rf'(?s)<div class="{name}">(.*?)</div>', card)
    return _text(found.group(1)) if found else ""


def prize_dollars(prize):
    """'$2.4M Prize' -> '2400000'; blank when there is no amount."""
    found = re.search(r"\$([\d.,]+)\s*([KMB]?)", prize)
    if not found:
        return ""
    scale = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[found.group(2)]
    return str(round(float(found.group(1).replace(",", "")) * scale))


def parse(page):
    """(path, title, description, stage, prize) for every challenge card."""
    cards = [(path, _part(card, "title"), _part(card, "description"), _part(card, "stage"), _part(card, "award"))
             for path, card in _CARD.findall(page)]
    if not cards:
        # Say what came back instead, so the log shows whether the layout
        # changed or HeroX sent a different page (such as a bot check).
        title = re.search(r"(?is)<title[^>]*>(.*?)</title>", page)
        got = _text(title.group(1)) if title else _text(page)[:120]
        raise ValueError(f"HeroX page has no challenge cards; got {len(page)} characters titled {got!r}")
    return cards


def normalize(path, title, description, stage, prize, today):
    left = re.search(r"(\d+)\s+Days? Remaining", stage)
    return {
        "source": "american-made",
        "source_id": path.strip("/"),
        "title": title,
        "funder": "Department of Energy (American-Made)",
        "funder_code": "DOE",
        "listing_type": "Prize",
        "status": "posted",
        "post_date": "",
        # The card counts the days left, so the deadline is today plus that.
        "close_date": (today + datetime.timedelta(days=int(left.group(1)))).isoformat() if left else "",
        "award_floor": "",
        "award_ceiling": "",
        "total_funding": prize_dollars(prize),
        "eligibility": "Others (see listing)",
        "topics": "Prize",
        "location": "National",
        "link": BASE + path,
        "summary": " ".join(p for p in (description, f"{prize}." if prize else "") if p),
    }


def collect(today, page=None):
    """Return American-Made prizes open for entries, in the common format.

    Pass page (the HeroX page HTML) to skip the download, e.g. in tests.
    """
    if page is None:
        page = fetch(PAGE_URL, timeout=60).decode("utf-8", "replace")
    return [normalize(*card, today) for card in parse(page) if card[3].startswith("Enter")]
