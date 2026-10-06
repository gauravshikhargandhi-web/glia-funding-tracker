import datetime
import json
import os
import unittest

from tracker import bonfire, california, chicago, federalregister, grantsgov, mwrd, nyc, pool, profile, samgov, text

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



def _read(name, encoding="utf-8"):
    with open(os.path.join(HERE, name), encoding=encoding) as f:
        return f.read()


class MwrdTest(unittest.TestCase):
    def setUp(self):
        self.rows = {r["source_id"]: r for r in mwrd.collect(
            TODAY, page=_read("sample_mwrd.html"), details={"2904": _read("sample_mwrd_detail.html")})}

    def test_keeps_bids_not_yet_opened(self):
        self.assertEqual(set(self.rows), {"23-890-1S", "25-RFP-20"})

    def test_normalizes_fields(self):
        row = self.rows["23-890-1S"]
        self.assertEqual(row["title"], "Rehabilitation Of Local Sewers")
        self.assertEqual((row["post_date"], row["close_date"]), ("2026-09-16", "2026-10-27"))
        self.assertEqual(row["award_ceiling"], "2706674")
        self.assertIn("LABOR AGREEMENT", row["summary"])
        self.assertTrue(row["link"].endswith("contractID=2904"))
        self.assertEqual(self.rows["25-RFP-20"]["listing_type"], "Contract (RFP)")


class ChicagoTest(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(HERE, "sample_chicago.html"), "rb") as f:
            page = chicago.decode(f.read())
        self.rows = {r["source_id"]: r for r in chicago.collect(TODAY, page=page)}

    def test_keeps_open_only(self):
        self.assertEqual(set(self.rows), {"70287", "72293"})

    def test_normalizes_fields(self):
        row = self.rows["70287"]
        self.assertEqual(row["funder"], "Chicago Department Of Water Management")
        self.assertEqual((row["post_date"], row["close_date"]), ("2026-09-14", "2026-10-14"))
        self.assertEqual(row["eligibility"], "Any vendor")
        self.assertEqual(self.rows["72293"]["funder"], "Chicago Department Of Aviation")
        self.assertEqual(self.rows["72293"]["title"], "AED\u2019s and Support Materials")

    def test_flags_target_market_set_aside(self):
        self.assertIn("Target Market", self.rows["72293"]["eligibility"])


class BonfireTest(unittest.TestCase):
    def test_keeps_open_and_normalizes(self):
        rows = bonfire.collect(TODAY, payloads={"glwater": json.loads(_read("sample_bonfire.json"))})
        self.assertEqual([r["source_id"] for r in rows], ["glwater-252183"])
        self.assertEqual(rows[0]["close_date"], "2026-10-16")
        self.assertEqual(rows[0]["funder"], "Great Lakes Water Authority")
        self.assertEqual(rows[0]["link"], "https://glwater.bonfirehub.com/opportunities/252183")


class FederalRegisterTest(unittest.TestCase):
    def test_drops_paperwork_notices_and_normalizes(self):
        rows = federalregister.collect(TODAY, data=json.loads(_read("sample_federalregister.json")))
        self.assertEqual([r["source_id"] for r in rows], ["2026-20001"])
        self.assertEqual(rows[0]["funder"], "National Oceanic and Atmospheric Administration")
        self.assertEqual(rows[0]["summary"], "NOAA invites applications for sensor pilots.")
        self.assertEqual(rows[0]["eligibility"], "Others (see listing)")


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

    def test_default_profile_keeps_every_water_agency_bid(self):
        rows = mwrd.collect(TODAY, page=_read("sample_mwrd.html"), details={})
        prof = profile.load(os.path.join(HERE, "..", "profile.toml"))
        ids = {r["source_id"] for r in profile.apply(prof, rows)}
        self.assertEqual(ids, {"23-890-1S", "25-RFP-20"})  # the CMMS software RFP has no water words

    def test_default_profile_keeps_only_allowed_contract_codes(self):
        with open(os.path.join(HERE, "sample_samgov.csv"), encoding="cp1252") as f:
            rows = samgov.collect(TODAY, csv_text=f.read())
        construction = dict(rows[0], source_id="c1", topics="NAICS 237110; PSC Y1ND")
        boat_part = dict(rows[0], source_id="c2", topics="NAICS 336612; PSC 2040")
        prof = profile.load(os.path.join(HERE, "..", "profile.toml"))
        ids = {r["source_id"] for r in profile.apply(prof, rows + [construction, boat_part])}
        self.assertEqual(ids, {"s6", "s2"})



class TextTest(unittest.TestCase):
    def test_drop_default_port(self):
        self.assertEqual(text.drop_default_port("https://s3.amazonaws.com:443/b/f.csv?X-Amz-Signature=abc"),
                         "https://s3.amazonaws.com/b/f.csv?X-Amz-Signature=abc")
        self.assertEqual(text.drop_default_port("https://example.com:8443/x"), "https://example.com:8443/x")
        self.assertEqual(text.drop_default_port("https://example.com/x"), "https://example.com/x")


class SamGovTest(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(HERE, "sample_samgov.csv"), encoding="cp1252") as f:
            self.rows = {r["source_id"]: r for r in samgov.collect(TODAY, csv_text=f.read())}

    def test_keeps_open_solicitations_and_early_notices(self):
        # s3 is an award, s4 is past its deadline, s5 has no deadline and is not an early notice,
        # and s6 is a later amendment of s1, so it replaces s1.
        self.assertEqual(set(self.rows), {"s6", "s2"})

    def test_normalizes_fields(self):
        row = self.rows["s6"]
        self.assertEqual(row["title"], "Stormwater sensor network pilot - Amendment 1")
        self.assertEqual(row["funder"], "National Oceanic And Atmospheric Administration")
        self.assertEqual(row["listing_type"], "Contract (Solicitation)")
        self.assertEqual(row["close_date"], "2026-11-05")
        self.assertEqual(row["eligibility"], "Small Business Set Aside - Total")
        self.assertEqual(row["topics"], "NAICS 334519; PSC 6665")
        self.assertEqual(row["location"], "Ann Arbor, MI")
        self.assertEqual(row["summary"], "Deploy sensors & telemetry.")

    def test_early_notice_without_deadline(self):
        row = self.rows["s2"]
        self.assertEqual(row["status"], "forecast")
        self.assertEqual(row["close_date"], "")
        self.assertEqual(row["eligibility"], "Any vendor")
        self.assertEqual(row["location"], "National")


if __name__ == "__main__":
    unittest.main()
