"""Collector for Great Lakes Commission requests for proposals.

The Commission posts its RFPs (sediment and nutrient reduction, invasive
species, nature-based stormwater, ...) as news items, a few each year, and
their web addresses contain "rfp". The first news pages are read, each RFP
post is opened for its deadline, and RFPs whose deadline has passed are
dropped. A post with no deadline counts for 120 days.
"""

import datetime
import html
import re

from tracker.text import clean, fetch

NEWS_URL = "https://www.glc.org/news/"
PAGES = 3
MAX_AGE_DAYS = 120

_ARTICLE = re.compile(r'(?s)<h2 class="entry-title">\s*<a href="([^"]+)">(.*?)</a>.*?class="published">(.*?)<')
_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
# "The deadline for submissions is 5 p.m. Eastern on April 30, 2026"; the year is sometimes left out.
_DEADLINE = re.compile(rf"(?:due|deadline|submitted by|no later than|close)(?:[^.]|\b[ap]\.m\.){{0,80}}?\b({_MONTHS})\s+(\d{{1,2}})(?:,?\s+(\d{{4}}))?",
                       re.IGNORECASE)


def _text(fragment):
    return re.sub(r"\s+", " ", html.unescape(clean(fragment))).strip()


def _date(text, fmt):
    try:
        return datetime.datetime.strptime(text.replace(".", "").strip(), fmt).date()
    except ValueError:
        return None


def parse_news(page):
    """(link, title, posted date) for each RFP post on a news page."""
    posts = []
    for link, title, posted in _ARTICLE.findall(page):
        if "rfp" in link.rstrip("/").rsplit("/", 1)[-1].lower():
            posts.append((link, _text(title), _date(posted, "%b %d, %Y")))
    return posts


def parse_post(page, posted=None):
    """(deadline or None, text) of an RFP post. A deadline without a year is
    taken as the first such date after the post date."""
    body = re.search(r"(?s)<article\b.*?</article>", page)
    text = _text(body.group(0) if body else "")
    found = _DEADLINE.search(text)
    if not found:
        return None, text
    month, day, year = found.groups()
    if year:
        return _date(f"{month} {day} {year}", "%B %d %Y"), text
    base = posted or datetime.date.today()
    deadline = _date(f"{month} {day} {base.year}", "%B %d %Y")
    if deadline and deadline < base:
        deadline = _date(f"{month} {day} {base.year + 1}", "%B %d %Y")
    return deadline, text


def collect(today, pages=None, posts=None):
    """Return the Commission's open RFPs in the common format.

    Pass pages (news page HTML) and posts (link -> post HTML) to skip the
    download, e.g. in tests.
    """
    if pages is None:
        pages = [fetch(NEWS_URL if n == 1 else f"{NEWS_URL}page/{n}/", timeout=60).decode("utf-8", "replace")
                 for n in range(1, PAGES + 1)]
    if not any(_ARTICLE.search(p) for p in pages):
        raise ValueError("Great Lakes Commission news layout changed: no posts found")
    rows = []
    for page in pages:
        for link, title, posted in parse_news(page):
            if posts is not None:
                post = posts.get(link, "")
            else:
                post = fetch(link, timeout=60).decode("utf-8", "replace")
            deadline, text = parse_post(post, posted)
            if deadline:
                if deadline < today:
                    continue
            elif not posted or (today - posted).days > MAX_AGE_DAYS:
                continue
            rows.append({
                "source": "glc",
                "source_id": link.rstrip("/").rsplit("/", 1)[-1],
                "title": re.sub(r"^Request for Proposals:\s*", "", title),
                "funder": "Great Lakes Commission",
                "funder_code": "GLC",
                "listing_type": "Grant (request for proposals)",
                "status": "posted",
                "post_date": posted.isoformat() if posted else "",
                "close_date": deadline.isoformat() if deadline else "",
                "award_floor": "",
                "award_ceiling": "",
                "total_funding": "",
                "eligibility": "Others (see listing)",
                "topics": "Great Lakes",
                "location": "Great Lakes region",
                "link": link,
                "summary": text,
            })
    return rows
