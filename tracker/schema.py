"""The common listing format every source is normalized into."""

FIELDS = [
    "source",          # where the listing came from, e.g. "grants.gov"
    "source_id",       # the source's own id, used to update rows day to day
    "title",
    "funder",          # agency, state department or city
    "funder_code",
    "listing_type",    # grant, cooperative agreement, contract, prize, ...
    "status",          # posted or forecast
    "post_date",       # YYYY-MM-DD
    "close_date",      # YYYY-MM-DD, blank for rolling or forecast
    "award_floor",     # dollars, blank when not given
    "award_ceiling",
    "total_funding",
    "eligibility",     # source's applicant types, "; " separated
    "topics",          # source's categories, "; " separated
    "location",        # where the applicant or work must be; "National" for federal
    "link",            # the original listing page
    "summary",         # first part of the description
    "first_seen",      # date this pool first saw the listing
    "last_seen",       # most recent date it was still open
]
