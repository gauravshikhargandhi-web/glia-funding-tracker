import datetime
import json
import os
import unittest

from tracker import california, grantsgov, nyc, pool, profile

HERE = os.path.dirname(__file__)
SAMPLE = os.path.join(HERE, "sample_extract.xml")
TODAY = datetime.date(2026, 10, 5)


class GrantsGovTest(unittest.TestCase):
    def setUp(self):
        self.rows = {r["source_id"]: r for r in grantsgov.collect(TODAY, xml_source=SAMPLE)}

    def test_keeps_open_and_forecast_only(self):
        self.assertEqual(set(self.rows), {"100", "102", "103"})

    def test_normalizes_fields(self):
        row = self.rows["100"]
        self.assertEqual(row["close_date"], "2026-12-15")
        self.assertEqual(row["award_ceiling"], "250000")
        self.assertEqual(row["eligibility"], "Small businesses")
        self.assertEqual(row["topics"], "Environment")
        self.assertEqual(row["listing_type"], "Grant")
        self.assertEqual(row["summary"], "Pilots that monitor shoreline & harbor structures.")
        self.assertEqual(row["link"], "https://www.grants.gov/search-results-detail/100")

    def test_forecast_status(self):
        self.assertEqual(self.rows["103"]["status"], "forecast")
        self.assertEqual(self.rows["103"]["close_date"], "")


class CaliforniaTest(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(HERE, "sample_california.csv"), encoding="utf-8") as f:
            self.rows = {r["source_id"]: r for r in california.collect(TODAY, csv_text=f.read())}

    def test_keeps_active_only(self):
        self.assertEqual(set(self.rows), {"192465", "190509"})

    def test_normalizes_fields(self):
        row = self.rows["192465"]
        self.assertEqual(row["close_date"], "2026-11-25")
        self.assertEqual((row["award_floor"], row["award_ceiling"]), ("1", "750000"))
        self.assertEqual(row["total_funding"], "15000000")
        self.assertEqual(row["eligibility"], "Business")
        self.assertEqual(row["location"], "California")
        self.assertTrue(row["link"].startswith("http"))

    def test_ongoing_deadline_is_blank(self):
        self.assertEqual(self.rows["190509"]["close_date"], "")


class NycTest(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(HERE, "sample_nyc.json"), encoding="utf-8") as f:
            self.rows = nyc.collect(TODAY, rows=json.load(f))

    def test_keeps_future_due_dates_only(self):
        self.assertEqual([r["source_id"] for r in self.rows], ["20260903027"])

    def test_normalizes_fields(self):
        row = self.rows[0]
        self.assertEqual(row["close_date"], "2026-10-08")
        self.assertEqual(row["funder"], "NYC Environmental Protection")
        self.assertEqual(row["listing_type"], "Contract (Request for Proposals)")
        self.assertEqual(row["summary"], "Sensors for sewer overflow monitoring.")
        self.assertEqual(row["link"], "https://a856-cityrecord.nyc.gov/RequestDetail/20260903027")


class PoolTest(unittest.TestCase):
    def test_merge_keeps_first_seen_and_other_sources(self):
        previous = [
            {"source": "grants.gov", "source_id": "100", "first_seen": "2026-09-01"},
            {"source": "grants.gov", "source_id": "999", "first_seen": "2026-08-01"},
            {"source": "nyc", "source_id": "A", "first_seen": "2026-09-15"},
        ]
        fresh = [{"source": "grants.gov", "source_id": "100"}, {"source": "grants.gov", "source_id": "200"}]
        merged = {r["source_id"]: r for r in pool.merge(previous, "grants.gov", fresh, TODAY)}
        self.assertEqual(set(merged), {"100", "200", "A"})  # 999 closed and dropped
        self.assertEqual(merged["100"]["first_seen"], "2026-09-01")
        self.assertEqual(merged["200"]["first_seen"], "2026-10-05")
        self.assertEqual(merged["100"]["last_seen"], "2026-10-05")


class ProfileTest(unittest.TestCase):
    def test_default_profile_filters_by_keyword_and_eligibility(self):
        rows = grantsgov.collect(TODAY, xml_source=SAMPLE)
        prof = profile.load(os.path.join(HERE, "..", "profile.toml"))
        ids = {r["source_id"] for r in profile.apply(prof, rows)}
        # 102 is water-related but open to universities only.
        self.assertEqual(ids, {"100", "103"})

    def test_default_profile_keeps_matching_city_solicitations(self):
        with open(os.path.join(HERE, "sample_nyc.json"), encoding="utf-8") as f:
            rows = nyc.collect(datetime.date(2026, 7, 1), rows=json.load(f))
        prof = profile.load(os.path.join(HERE, "..", "profile.toml"))
        ids = {r["source_id"] for r in profile.apply(prof, rows)}
        self.assertEqual(ids, {"20260903027"})  # the locks bid has no water keywords


if __name__ == "__main__":
    unittest.main()
