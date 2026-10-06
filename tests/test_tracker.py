import datetime
import json
import os
import unittest

from tracker import (bonfire, california, chicago, federalregister, grantsgov, illinois, massachusetts,
                     mwrd, nyc, plain, pool, prizes, profile, samgov, text, virginia)

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



class IllinoisTest(unittest.TestCase):
    def setUp(self):
        self.rows = {r["source_id"]: r for r in illinois.collect(TODAY, page=_read("sample_illinois.html"))}

    def test_keeps_open_and_no_end_date(self):
        self.assertEqual(set(self.rows), {"0f9fad21-8730", "4339"})

    def test_normalizes_fields(self):
        row = self.rows["0f9fad21-8730"]
        self.assertEqual(row["title"], "Lake Michigan Monitoring")
        self.assertEqual(row["funder"], "Illinois Department of Natural Resources")
        self.assertEqual((row["award_floor"], row["award_ceiling"]), ("15000", "75000"))
        self.assertEqual(row["close_date"], "")
        self.assertEqual(row["link"], "https://il.amplifund.com/Public/Opportunities/Details/0f9fad21-8730")
        nofo = self.rows["4339"]
        self.assertEqual((nofo["post_date"], nofo["close_date"]), ("2026-08-31", "2026-10-19"))
        self.assertTrue(nofo["link"].endswith("nofo=4339"))


class MassachusettsTest(unittest.TestCase):
    def test_pages_are_combined_deduped_and_filtered(self):
        pages = [_read("sample_commbuys_p1.html"), _read("sample_commbuys_p2.xml")]
        rows = {r["source_id"]: r for r in massachusetts.collect(TODAY, pages=pages)}
        self.assertEqual(set(rows), {"BD-1", "BD-2"})
        self.assertEqual(rows["BD-1"]["listing_type"], "Grant")
        self.assertEqual(rows["BD-1"]["close_date"], "2026-11-06")
        self.assertEqual(rows["BD-2"]["funder"], "City of Fitchburg")
        self.assertIn("docId=BD-2", rows["BD-2"]["link"])


class VirginiaTest(unittest.TestCase):
    def test_keeps_open_future_and_normalizes(self):
        rows = virginia.collect(TODAY, data=json.loads(_read("sample_virginia.json")))
        self.assertEqual([r["source_id"] for r in rows], ["VBO:IFB:A123:1"])
        row = rows[0]
        self.assertEqual((row["post_date"], row["close_date"]), ("2026-09-01", "2026-11-01"))
        self.assertEqual(row["summary"], "Furnish sensors .")
        self.assertEqual(row["topics"], "Water Testing Equipment")
        self.assertEqual(row["location"], "Virginia Beach, VA")
        self.assertIn("VBODetails.jsp", row["link"])
        self.assertIn("BID_INTRNL_NO=1", row["link"])

    def test_local_government_bids_link_to_their_own_page(self):
        link = virginia._link({"app": "IV", "internalid": "128282", "version": "1"})
        self.assertEqual(link, "https://mvendor.cgieva.com/Vendor/public/IVDetails.jsp?"
                               "PageTitle=SO+Details&rfp_id_lot=128282&rfp_id_round=1")


class PrizesTest(unittest.TestCase):
    def test_reads_open_xtech_cards_and_skips_empty_usbr_page(self):
        rows = prizes.collect(TODAY, xtech_page=_read("sample_xtech.html"), usbr_page=_read("sample_usbr_none.html"))
        self.assertEqual([r["source_id"] for r in rows], ["xtechsearch10"])
        row = rows[0]
        self.assertEqual(row["title"], "xTech|Search 10")
        self.assertEqual((row["post_date"], row["close_date"]), ("2026-09-10", "2026-10-19"))
        self.assertIn("unmanned vessel", row["summary"])

    def test_usbr_page_with_a_competition_is_listed(self):
        page = _read("sample_usbr_none.html").replace(
            "There are currently no prize competitions accepting submissions.", "Halt the Hitchhiker Phase 2 is open.")
        rows = prizes.parse_usbr(page, TODAY)
        self.assertEqual(len(rows), 1)
        self.assertIn("Halt the Hitchhiker", rows[0]["summary"])
        self.assertEqual(rows[0]["source_id"], prizes.parse_usbr(page, TODAY)[0]["source_id"])


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
        dropped = []
        ids = {r["source_id"] for r in profile.apply(prof, rows, dropped)}
        self.assertEqual(ids, {"25-RFP-20"})  # the CMMS software RFP has no water words
        # The sewer rehabilitation bid matches as a water-agency bid but is construction.
        self.assertEqual([row["source_id"] for row, _ in dropped], ["23-890-1S"])

    def test_default_profile_keeps_only_allowed_contract_codes(self):
        with open(os.path.join(HERE, "sample_samgov.csv"), encoding="cp1252") as f:
            rows = samgov.collect(TODAY, csv_text=f.read())
        construction = dict(rows[0], source_id="c1", topics="NAICS 237110; PSC Y1ND")
        boat_part = dict(rows[0], source_id="c2", topics="NAICS 336612; PSC 2040")
        prof = profile.load(os.path.join(HERE, "..", "profile.toml"))
        ids = {r["source_id"] for r in profile.apply(prof, rows + [construction, boat_part])}
        self.assertEqual(ids, {"s6", "s2"})

    def test_who_can_bid_rules_drop_and_record_reasons(self):
        base = {k: "" for k in pool.FIELDS}
        base.update(title="Stormwater monitoring", summary="water quality", eligibility="Any vendor",
                    funder="City", listing_type="Contract (bid)")
        rows = [
            dict(base, source_id="keep"),
            dict(base, source_id="setaside", eligibility="Total Small Business; 8(a) Set-Aside"),
            dict(base, source_id="build", title="Water Main Replacement Phase 2"),
            dict(base, source_id="grant", title="Water Main Replacement Planning Grant",
                 listing_type="Grant", eligibility="Others (see listing)"),
            dict(base, source_id="category", title="Stormwater pond retrofit", topics="Category: Construction"),
            dict(base, source_id="locating", title="Locating Underground Water & Sanitary Sewer",
                 topics="Category: Construction"),
            dict(base, source_id="noprofit", listing_type="Grant", eligibility="Others (see listing)",
                 eligibility_notes="For-profit organizations are not eligible to apply."),
            dict(base, source_id="seelisting", listing_type="Grant", eligibility="Others (see listing)",
                 eligibility_notes="See the full announcement for details."),
        ]
        prof = profile.load(os.path.join(HERE, "..", "profile.toml"))
        dropped = []
        ids = {r["source_id"] for r in profile.apply(prof, rows, dropped)}
        self.assertEqual(ids, {"keep", "grant", "seelisting", "locating"})
        reasons = {row["source_id"]: reason for row, reason in dropped}
        self.assertEqual(reasons["setaside"], "set-aside: 8(a)")
        self.assertEqual(reasons["build"], "construction bid: water main replacement")
        self.assertEqual(reasons["category"], "construction bid: Category: Construction")
        self.assertNotIn("locating", reasons)
        self.assertTrue(reasons["noprofit"].startswith("not open to businesses"))



class PlainTest(unittest.TestCase):
    def row(self, **fields):
        base = {k: "" for k in pool.FIELDS}
        base.update(fields)
        return plain.describe(base)

    def test_grant_with_ceiling_and_see_listing(self):
        got = self.row(listing_type="Cooperative agreement; Grant", status="posted", close_date="2026-11-01",
                       award_ceiling="1657690", eligibility="Others (see listing)",
                       summary="Study salinity &amp;amp; flow. More detail follows.")
        self.assertEqual(got["kind"], "Grant")
        self.assertEqual(got["stage"], "Open")
        self.assertEqual(got["deadline"], "2026-11-01")
        self.assertEqual(got["amount"], "Up to $1.7M")
        self.assertEqual(got["who_can_apply"], "Check listing")
        self.assertEqual(got["short_summary"], "Study salinity & flow. More detail follows.")

    def test_contract_stages_and_set_asides(self):
        sought = self.row(listing_type="Contract (Sources Sought)", status="forecast",
                          eligibility="Small Business Set Aside - Total")
        self.assertEqual((sought["kind"], sought["stage"], sought["who_can_apply"]),
                         ("Contract", "Info request", "Small businesses only"))
        presol = self.row(listing_type="Contract (Presolicitation)", status="forecast", eligibility="Any vendor")
        self.assertEqual((presol["stage"], presol["deadline"], presol["who_can_apply"]),
                         ("Coming soon", "Not set", "Any company"))

    def test_total_funding_and_long_summary(self):
        got = self.row(listing_type="Grant", total_funding="3500000", eligibility="Business; Nonprofit",
                       summary="word " * 100)
        self.assertEqual(got["amount"], "$3.5M total")
        self.assertEqual(got["who_can_apply"], "Companies eligible")
        self.assertTrue(got["short_summary"].endswith(" ...") and len(got["short_summary"]) <= 284)


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
