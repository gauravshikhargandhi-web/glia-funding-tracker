"""Small text helpers shared by the collectors."""

import re


def clean(text):
    """Strip HTML tags and entities and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def dollars(text):
    """'$1,250,000.00' -> '1250000'; blank when there is no usable amount."""
    match = re.search(r"\$?\s*([\d,]+)(?:\.\d+)?", text or "")
    if not match:
        return ""
    value = match.group(1).replace(",", "")
    return value if value.strip("0") else ""
