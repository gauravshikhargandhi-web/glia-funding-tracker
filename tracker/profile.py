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


def apply(profile, rows):
    rules = profile.get("filter", {})
    include = _pattern(rules.get("keywords", []))
    exclude = _pattern(rules.get("exclude_keywords", []))
    eligible = [e.lower() for e in rules.get("eligibility_any", [])]
    skip_funders = tuple(rules.get("exclude_funder_codes", []))
    skip_topics = rules.get("exclude_topics", [])
    allowed_codes = rules.get("allowed_codes", [])
    water_agencies = [a.lower() for a in rules.get("water_agencies", [])]

    matches = []
    for row in rows:
        text = f"{row['title']} {row['summary']}"
        from_water_agency = any(a in row["funder"].lower() for a in water_agencies)
        if include and not from_water_agency and not include.search(text):
            continue
        if exclude and exclude.search(text):
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
