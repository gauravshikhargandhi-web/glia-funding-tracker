"""Small helpers shared by the collectors."""

import re
import urllib.request

# Some portals (data.ca.gov among them) refuse Python's default user agent.
USER_AGENT = "Mozilla/5.0 (compatible; glia-funding-tracker; +https://github.com/gauravshikhargandhi-web/glia-funding-tracker)"


def fetch(url, timeout=300):
    """Download a URL and return its bytes."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return resp.read()


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
