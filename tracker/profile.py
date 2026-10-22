"""A simple profile filter that narrows the pool to what one founder cares about.

This is deliberately basic (keywords plus eligibility); proper matching comes later.
"""

import re
import tomllib

from tracker import plain


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


def apply(profile, rows, dropped=None, keep=()):
    """Return the rows that fit the profile.

    Pass a list as dropped to collect (row, reason) for listings that matched
    the keywords but were removed by the "who can bid" rules, for review.
    Pass keep, a set of (source, source_id), to keep yesterday's matches whose
    full text is not at hand (their source failed today, so only the cut
    summary was loaded from listings.csv).
    """
    rules = profile.get("filter", {})
    topic = _topic_rules(rules)
    eligible = [e.lower() for e in rules.get("eligibility_any", [])]
    skip_funders = tuple(rules.get("exclude_funder_codes", []))
    skip_topics = rules.get("exclude_topics", [])
    allowed_codes = rules.get("allowed_codes", [])
    set_asides = [a.lower() for a in rules.get("exclude_set_asides", [])]
    contractor_words = _pattern(rules.get("contractor_only_title_words", []))
    contractor_topics = rules.get("contractor_only_topics", [])
    off_topic_words = _pattern(rules.get("off_topic_title_words", []))
    tech_words = _pattern(rules.get("not_construction_words", []))
    not_eligible = _regex(rules.get("not_eligible_patterns", []))
    partner_text = _regex(rules.get("partner_needed_patterns", []))
    partner_types = [e.lower() for e in rules.get("partner_needed_eligibility", [])]
    tech_bid_words = _pattern(rules.get("tech_bid_words", []))
    label_skip = rules.get("maintenance_label_skip_sources", [])

    matches = []
    for row in rows:
        if not _on_topic(row, topic, keep):
            continue
        partner = _partner_needed(row, partner_text, partner_types, eligible)
        reason = _who_can_bid(row, set_asides, contractor_words, contractor_topics, tech_words,
                              None if partner else not_eligible, off_topic_words)
        if reason:
            if dropped is not None:
                dropped.append((row, reason))
            continue
        if not partner and eligible and not any(e in row["eligibility"].lower() for e in eligible):
            continue
        if not _is_research(row, topic["research"]):
            if skip_funders and row["funder_code"].startswith(skip_funders):
                continue
            if any(t in row["topics"] for t in skip_topics):
                continue
            # Listings that carry a product/service code (SAM.gov) must use an allowed one.
            if allowed_codes and _CODE.search(row["topics"]) and not any(c in row["topics"] for c in allowed_codes):
                continue
        changes = {}
        if partner:
            changes["who_can_apply"] = "Partner needed"
        if tech_bid_words and _maintenance_bid(row, tech_bid_words, label_skip):
            changes["kind"] = "Construction/maintenance"
        matches.append(dict(row, **changes) if changes else row)
    return matches


def on_topic(profile, rows, keep=()):
    """The rows that match the keywords (or come from a water agency or research
    funder), before any eligibility or "who can bid" rule. Used to decide what
    goes in the archive."""
    topic = _topic_rules(profile.get("filter", {}))
    return [r for r in rows if _on_topic(r, topic, keep)]


def _topic_rules(rules):
    return {
        "include": _pattern(rules.get("keywords", [])),
        "exclude": _pattern(rules.get("exclude_keywords", [])),
        "water_agencies": [a.lower() for a in rules.get("water_agencies", [])],
        "research": _pattern(rules.get("research_funders", [])),
        "picked": rules.get("hand_picked_sources", []),
    }


def _on_topic(row, topic, keep=()):
    if row["source"] in topic["picked"] or _is_research(row, topic["research"]):
        return True
    if "match_text" not in row and (row["source"], row["source_id"]) in keep:
        return True
    from_water_agency = any(a in row["funder"].lower() for a in topic["water_agencies"])
    # Keywords are looked for in the full description; exclusions only in the
    # title and cut summary, so boilerplate deep in a notice doesn't drop it.
    full_text = f"{row['title']} {row.get('match_text') or row['summary']}"
    if topic["include"] and not from_water_agency and not topic["include"].search(full_text):
        return False
    return not (topic["exclude"] and topic["exclude"].search(f"{row['title']} {row['summary']}"))


def _is_research(row, research):
    return bool(research and research.search(f"{row['title']} {row['funder']}"))


def _partner_needed(row, partner_text, partner_types, eligible):
    """True for grants open only to universities, which a startup can join as a partner."""
    if partner_text and partner_text.search(f"{row.get('eligibility_notes', '')} {row.get('match_text') or row['summary']}"):
        return True
    types = row["eligibility"].lower()
    return any(t in types for t in partner_types) and not any(e in types for e in eligible)


def _maintenance_bid(row, tech_bid_words, skip_sources):
    """A local or utility bid for building, repair, supplies or services rather
    than technology: a contract that isn't an info request and whose title has
    no technology, pilot or information-request word."""
    return (row["listing_type"].startswith("Contract") and row["source"] not in skip_sources
            and plain.stage(row) != "Info request" and not tech_bid_words.search(row["title"]))


def _who_can_bid(row, set_asides, contractor_words, contractor_topics, tech_words, not_eligible,
                 off_topic_words=None):
    """Why a startup could not bid on this listing, or "" if nothing says so."""
    eligibility = row["eligibility"].lower()
    for name in set_asides:
        if name in eligibility:
            return f"set-aside: {name}"
    looks_technical = tech_words and tech_words.search(row["title"])
    if row["listing_type"].startswith("Contract") and not looks_technical:
        found = contractor_words.search(row["title"]) if contractor_words else None
        if found:
            return f"construction bid: {found.group(0).lower()}"
        for topic in contractor_topics:
            if topic in row["topics"]:
                return f"construction bid: {topic}"
        found = off_topic_words.search(row["title"]) if off_topic_words else None
        if found:
            return f"off-topic bid: {found.group(0).lower()}"
    if not_eligible:
        found = not_eligible.search(f"{row.get('eligibility_notes', '')} {row.get('match_text') or row['summary']}")
        if found:
            return f"not open to businesses: {found.group(0)}"
    return ""
