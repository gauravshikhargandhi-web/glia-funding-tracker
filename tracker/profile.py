"""A simple profile filter that narrows the pool to what one founder cares about.

This is deliberately basic (keywords plus eligibility); proper matching comes later.
"""

import re
import tomllib


def load(path):
    with open(path, "rb") as f:
        return tomllib.load(f)


_CODE = re.compile(r"PSC \w")


def _pattern(words):
    if not words:
        return None
    return re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")", re.IGNORECASE)


def _regex(patterns):
    if not patterns:
        return None
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)


def apply(profile, rows, dropped=None):
    """Return the rows that fit the profile.

    Pass a list as dropped to collect (row, reason) for listings that matched
    the keywords but were removed by the "who can bid" rules, for review.
    """
    rules = profile.get("filter", {})
    include = _pattern(rules.get("keywords", []))
    exclude = _pattern(rules.get("exclude_keywords", []))
    eligible = [e.lower() for e in rules.get("eligibility_any", [])]
    skip_funders = tuple(rules.get("exclude_funder_codes", []))
    skip_topics = rules.get("exclude_topics", [])
    allowed_codes = rules.get("allowed_codes", [])
    water_agencies = [a.lower() for a in rules.get("water_agencies", [])]
    set_asides = [a.lower() for a in rules.get("exclude_set_asides", [])]
    contractor_words = _pattern(rules.get("contractor_only_title_words", []))
    contractor_topics = rules.get("contractor_only_topics", [])
    not_eligible = _regex(rules.get("not_eligible_patterns", []))

    matches = []
    for row in rows:
        text = f"{row['title']} {row['summary']}"
        from_water_agency = any(a in row["funder"].lower() for a in water_agencies)
        if include and not from_water_agency and not include.search(text):
            continue
        if exclude and exclude.search(text):
            continue
        reason = _who_can_bid(row, set_asides, contractor_words, contractor_topics, not_eligible)
        if reason:
            if dropped is not None:
                dropped.append((row, reason))
            continue
        if eligible and not any(e in row["eligibility"].lower() for e in eligible):
            continue
        if skip_funders and row["funder_code"].startswith(skip_funders):
            continue
        if any(t in row["topics"] for t in skip_topics):
            continue
        # Listings that carry a product/service code (SAM.gov) must use an allowed one.
        if allowed_codes and _CODE.search(row["topics"]) and not any(c in row["topics"] for c in allowed_codes):
            continue
        matches.append(row)
    return matches


def _who_can_bid(row, set_asides, contractor_words, contractor_topics, not_eligible):
    """Why a startup could not bid on this listing, or "" if nothing says so."""
    eligibility = row["eligibility"].lower()
    for name in set_asides:
        if name in eligibility:
            return f"set-aside: {name}"
    if row["listing_type"].startswith("Contract"):
        found = contractor_words.search(row["title"]) if contractor_words else None
        if found:
            return f"construction bid: {found.group(0).lower()}"
        for topic in contractor_topics:
            if topic in row["topics"]:
                return f"construction bid: {topic}"
    if not_eligible:
        found = not_eligible.search(f"{row.get('eligibility_notes', '')} {row['summary']}")
        if found:
            return f"not open to businesses: {found.group(0)}"
    return ""
