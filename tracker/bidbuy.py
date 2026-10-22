"""Collector for Illinois BidBuy open bids (state agencies and universities).

BidBuy runs on the same platform as Massachusetts COMMBUYS, so this reads it
with the COMMBUYS collector pointed at BidBuy's host.
"""

from tracker import massachusetts

SITE = {"host": "https://www.bidbuy.illinois.gov", "source": "bidbuy-illinois", "code": "IL", "location": "Illinois"}


def collect(today, pages=None):
    """Return open BidBuy bids in the common format.

    Pass pages (the result pages' HTML) to skip the download, e.g. in tests.
    """
    return massachusetts.collect(today, pages, **SITE)
