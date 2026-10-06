"""Daily run: pull every source, refresh the pool, write the profile matches.

    python -m tracker.run                 # normal daily run
    python -m tracker.run --xml FILE      # use a local Grants.gov extract
"""

import argparse
import datetime

from tracker import grantsgov, pool, profile

POOL_PATH = "data/listings.csv"
MATCHES_PATH = "data/matches.csv"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", help="local Grants.gov extract instead of downloading")
    parser.add_argument("--today", help="override today's date (YYYY-MM-DD)")
    parser.add_argument("--profile", default="profile.toml")
    args = parser.parse_args()

    today = datetime.date.fromisoformat(args.today) if args.today else datetime.date.today()
    rows = pool.load(POOL_PATH)

    fresh = grantsgov.collect(today, xml_source=args.xml)
    rows = pool.merge(rows, "grants.gov", fresh, today)
    print(f"grants.gov: {len(fresh)} open listings")

    pool.save(POOL_PATH, rows)
    matches = profile.apply(profile.load(args.profile), rows)
    pool.save(MATCHES_PATH, matches)
    print(f"pool: {len(rows)} listings, {len(matches)} match {args.profile}")


if __name__ == "__main__":
    main()
