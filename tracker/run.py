"""Daily run: pull every source, refresh the pool, write the profile matches.

    python -m tracker.run                 # normal daily run
    python -m tracker.run --xml FILE      # use a local Grants.gov extract
"""

import argparse
import datetime

from tracker import (bonfire, california, chicago, federalregister, grantsgov, illinois, massachusetts,
                     mwrd, nyc, pool, prizes, profile, samgov, virginia)

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

    sources = [
        ("grants.gov", lambda: grantsgov.collect(today, xml_source=args.xml)),
        ("grants.ca.gov", lambda: california.collect(today)),
        ("nyc-city-record", lambda: nyc.collect(today)),
        ("sam.gov", lambda: samgov.collect(today)),
        ("federalregister", lambda: federalregister.collect(today)),
        ("mwrd", lambda: mwrd.collect(today)),
        ("chicago-eprocurement", lambda: chicago.collect(today)),
        ("bonfire", lambda: bonfire.collect(today)),
        ("illinois-gata", lambda: illinois.collect(today)),
        ("commbuys", lambda: massachusetts.collect(today)),
        ("eva-virginia", lambda: virginia.collect(today)),
        ("prizes", lambda: prizes.collect(today)),
    ]
    failed = []
    for name, collect in sources:
        try:
            fresh = collect()
        except Exception as exc:
            # Keep yesterday's rows for this source and carry on with the rest.
            print(f"{name}: FAILED ({exc}); keeping previous listings")
            failed.append(name)
            continue
        rows = pool.merge(rows, name, fresh, today)
        print(f"{name}: {len(fresh)} open listings")

    pool.save(POOL_PATH, rows)
    matches = profile.apply(profile.load(args.profile), rows)
    pool.save(MATCHES_PATH, matches)
    print(f"pool: {len(rows)} listings, {len(matches)} match {args.profile}")
    if failed:
        raise SystemExit(f"sources failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
