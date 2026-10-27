# GLIA Funding Tracker

A free, self-running list of open funding opportunities for water and water-adjacent startups, built for the [gener8tor Great Lakes Innovation Accelerator](https://www.gener8tor.com/greatlakes) cohort. Founders can copy it and keep it running on their own GitHub account after the program, at no cost.

Every day a GitHub job pulls public funding sources, keeps the listings that are still open, and saves them in one common format.

## What's in it

| File | What it holds |
| --- | --- |
| [`data/listings.csv`](data/listings.csv) | Every open listing from every source |
| [`data/matches.csv`](data/matches.csv) | The listings that fit [`profile.toml`](profile.toml) |
| [`data/filtered_out.csv`](data/filtered_out.csv) | Listings that fit the keywords but were removed because a startup could not bid (certification-only set-aside, construction bid, off-topic bid for supplies or building services, or a grant that rules out businesses), with the reason in the last column |
| [`data/archive/`](data/archive) | Water listings that have closed, one file per year (starting 2026), kept for looking back at what funders offer and when |
| [`data/summary.csv`](data/summary.csv) | Today's counts per source and per kind, stage and who can apply (feeds the sheet's About tab) |
| [`profile.toml`](profile.toml) | Keywords and eligibility rules that decide what counts as a match |

Each row has the same columns whatever the source. Six plain columns come right after the title and funder, so every listing reads the same way:

| Column | Values |
| --- | --- |
| kind | Grant, Contract, Prize, Accelerator, Pitch competition, Pilot, Loan, Equity (investment programs), Funding notice; in `matches.csv`, Construction/maintenance marks a local or utility bid for building, repair, supplies or services rather than technology (see below) |
| stage | Open (apply now), Coming soon (announced, not open yet), Info request (the buyer is asking questions before a bid) |
| deadline | Closing date, or "Not set" for rolling and forecast listings |
| amount | "Up to $500K" from the award ceiling, or "$3.5M total" from total funding, when the source gives one |
| who_can_apply | Any company, Companies eligible, Small businesses only, Check listing, Not companies; in `matches.csv`, Partner needed marks a grant open only to universities, which a startup can join as a partner or subrecipient |
| short_summary | The first sentences of the summary |

The source's own wording follows: listing type, status, post and close dates, award floor and ceiling, total funding, eligibility, eligibility notes, topics, location, link, the summary (first 600 characters), and the dates the tracker first and last saw the listing.

## How matching works

The rules are in [`profile.toml`](profile.toml), each with a comment. In short:

- A listing matches when its title or full description has one of the `keywords`. The `summary` column only keeps the first 600 characters, but long federal notices often name the topic further down, so the whole text is searched.
- Every listing from a `water_agencies` funder, a `research_funders` funder (Army Corps ERDC, SERDP, ESTCP) or a `hand_picked_sources` source counts, whatever its words.
- The "who can bid" rules then set aside certification-only set-asides, construction and off-topic bids, and grants closed to companies, with the reason in `filtered_out.csv`.
- Grants open only to universities are kept with who_can_apply = Partner needed.
- Local and utility bids whose titles have no technology, pilot or information-request word (`tech_bid_words`) are kept with kind = Construction/maintenance, so they can be filtered out. Federal research and SBIR topics never get this label.

## Sources

| Source | Status | Key needed |
| --- | --- | --- |
| [Grants.gov](https://www.grants.gov) daily extract (all federal grants and forecasts) | Live | No |
| [California Grants Portal](https://data.ca.gov/dataset/california-grants-portal) (all California state grants and loans) | Live | No |
| [NYC City Record Online](https://a856-cityrecord.nyc.gov/) solicitations | Live | No |
| [SAM.gov](https://sam.gov) contract opportunities (public daily file of every federal contract notice) | Live | No |
| [Federal Register](https://www.federalregister.gov) funding, prize and proposal notices (last 30 days) | Live | No |
| [MWRD](https://apps.mwrd.org/ContractAnnouncements/) (Chicago water reclamation district) contract announcements | Live | No |
| [City of Chicago eProcurement](https://eprocurement.cityofchicago.org/OA_HTML/OA.jsp?OAFunc=PON_ABSTRACT_PAGE) solicitations | Live | No |
| [Great Lakes Water Authority](https://glwater.bonfirehub.com/portal/?tab=openOpportunities) (Detroit area) open bids on Bonfire | Live | No |
| Open bids on OpenGov: [Northeast Ohio Regional Sewer District](https://procurement.opengov.com/portal/neorsd) (Cleveland area), [City of Cleveland](https://procurement.opengov.com/portal/clevelandoh) and [City of Syracuse](https://procurement.opengov.com/portal/syrgov) | Live | No |
| [Milwaukee Metropolitan Sewerage District](https://mmsd.diversitycompliance.com/FrontEnd/proposalsearchpublic.asp?tn=mmsd&xid=8146) bids, RFPs and RFIs (construction bids on QuestCDN not covered) | Live | No |
| [Madison Metropolitan Sewerage District](https://www.madsewer.org/contracting-center/) bids and RFPs (deadline read from the notice; notices without one are kept 45 days) | Live | No |
| [Buffalo Sewer Authority](https://buffalosewer.org/category/vendor-opportunities/) bid and RFP posts (deadline read from the notice text) | Live | No |
| Chicago bids posted only in the weekly PDF; City of Detroit (site blocks automated access) | Not covered | |
| [Illinois GATA](https://omb.illinois.gov/public/gata/csfa/OpportunityList.aspx) state funding opportunities | Live | No |
| [Massachusetts COMMBUYS](https://www.commbuys.com/bso/view/search/external/advancedSearchBid.xhtml?openBids=true) open bids and grants (state, cities, authorities) | Live | No |
| [MassCEC](https://www.masscec.com/funding?status%5Bopen%5D=open) (Massachusetts Clean Energy Center) open grants, investments and programs; every program counts as a match | Live | No |
| [Virginia eVA](https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp) open solicitations (state, universities, localities) | Live | No |
| [Indiana state bids](https://www.in.gov/idoa/procurement/current-business-opportunities/) (IDOA current business opportunities; links go to each bid's documents) | Live | No |
| [Illinois BidBuy](https://www.bidbuy.illinois.gov/bso/view/search/external/advancedSearchBid.xhtml?openBids=true) open bids (state agencies and universities; same platform as COMMBUYS) | Live | No |
| [Pennsylvania eMarketplace](https://www.emarketplace.state.pa.us/Search.aspx) open solicitations (state agencies, universities and authorities) | Live | No |
| [Water Research Foundation](https://portal.waterrf.org/outbound-grants) open research RFPs | Live | No |
| [Great Lakes Commission](https://www.glc.org/news/) RFPs (posted as news; kept while the deadline is ahead) | Live | No |
| [H2Ohio](https://h2.ohio.gov/wps/portal/gov/h2ohio/partner-with-us/find-a-grant/find-a-grant) grant programs that are open or rolling | Live | No |
| [Ohio Third Frontier Technology Validation and Start-up Fund](https://development.ohio.gov/business/third-frontier-and-technology/technology-validation-start-up-fund), listed while a round is open; counts as a match | Live | No |
| [Great Lakes Restoration Initiative](https://glri.us/funding/funding-opportunities) open funding opportunities (USDA Forest Service, Ohio, NFWF and others; links to Grants.gov are skipped since Grants.gov is already a source) | Live | No |
| Prize competitions: [Army xTech](https://xtech.army.mil/competitions/) and [Bureau of Reclamation](https://www.usbr.gov/research/challenges/accepting.html) | Live | No |
| [DOE American-Made prizes](https://www.herox.com/American-Made-Challenges) open for entries (listed on HeroX; American-Made's own site needs a browser) | Live | No |
| [Federal prize challenges](https://www.usa.gov/find-active-challenge) listed on USA.gov, Challenge.gov's successor (student competitions skipped) | Live | No |
| [DOE Water Power Technologies Office](https://www.energy.gov/eere/water/funding-opportunities) funding and technical support (TEAMER and others); every listing counts as a match | Live | No |
| [NYSERDA](https://nyserda.ny.gov/All-Programs/Innovation-at-NYSERDA/Funding-Opportunities) current innovation calls (PONs and RFIs), with due dates from each call's portal page; NYSERDA's full list needs a browser | Live | No |
| [City of Cleveland](https://www.clevelandohio.gov/city-hall/departments/finance/invitations-bid) bids and [RFPs](https://www.clevelandohio.gov/city-hall/departments/finance/request-qualificationsproposal), including the Division of Water | Live | No |
| [Met Council](https://metrocouncil.org/About-Us/What-We-Do/DoingBusiness/Contracting-Opportunities.aspx) (Minneapolis-St. Paul) bids, RFPs and RFIs, including regional wastewater | Live | No |
| [SBIR.gov topics](https://www.sbir.gov/topics) from every agency (Defense, Energy, NASA, EPA, ...), open and upcoming; SBIR.gov's data API refuses automated requests, so the public topic search's Download (CSV) button is used | Live | No |
| [NSF SBIR/STTR](https://www.nsf.gov/funding/opportunities) deadlines in the next 30 days (NSF's other programs come through Grants.gov) | Live | No |
| Calendar of yearly programs (accelerators, prizes, grants with no feed), kept by hand in the Google Sheet's **Calendar** tab; see below | Live | No |
| Leads: news feeds of incubators, water clusters and funders (Evergreen Climate Innovations, The Water Council, Current, LACI, JumpStart, fundsforcompanies, GLOS, NAWI, ERDCWERX, mHUB, SeaAhead, Ocean Exchange, Climate Tech VC); see below | Live | No |
| Michigan EGLE (site refuses automated requests); Minnesota Pollution Control Agency (site sends automated requests to a bot check); Wisconsin VendorNet (state agencies, UW System and many cities; only works in a browser); City of Milwaukee and Port Milwaukee bids (sites refuse automated requests); NEW Water, Green Bay (no open projects to read yet); Wisconsin DNR Surface Water Grants and WEDC Entrepreneurship Partner Grants (yearly, for local governments and organizations; better in the Calendar tab); Minnesota state RFPs (robots.txt disallows automated access); Pennsylvania grants search (its CSV download only works inside a browser, through a third-party search service); Ohio Lake Erie Commission (program descriptions only, no open dates); NOAA Sea Grant (national notices also reach Grants.gov); CIGLR (feed refuses automated requests); Defense Innovation Unit (listings only render in a browser; many also reach SAM.gov); Greentown Labs (no feed; its challenges usually appear in the Climate Tech VC newsletter); SERDP/ESTCP site (unreliable; its calls also reach SAM.gov); other New York state grants (no open source found yet) | Not covered | |

If one source fails on a given day, the others still update and that source keeps its previous listings, and the About tab says so. A one-day outage is common, so the run only shows as failed in the Actions tab (and GitHub emails you) once a source has failed 3 days in a row; `data/failures.csv` keeps the count.

Only free, public sources are used. Sites that need a login are left out.

## Calendar of yearly programs

Some of the best programs for water startups (Imagine H2O, BREW, Techstars WaterTech, Cleantech Open, the Google water RFI) open once a year on pages with no feed. Their dates are kept by hand in the **Calendar** tab of the Google Sheet, one row per program per round:

| Column | What to put |
| --- | --- |
| program, run_by, kind | Name, who runs it, and Accelerator, Prize, Grant, Pilot or Pitch competition |
| opens, closes | Dates as YYYY-MM-DD; leave blank when not announced |
| rolling | "yes" for programs that take applications any time |
| amount, who_can_apply, location | e.g. "Up to $10K", "Any company" or "Illinois small businesses", "Milwaukee, WI" |
| usual_window | When it usually opens, e.g. "October to November", for planning next year |
| link, about, notes | The apply page and a sentence or two |
| last_checked | The date someone last confirmed the row |

Each morning the job reads the tab (the sheet must be shared as "anyone with the link can view"; the address is in `profile.toml` under `[calendar]`) and keeps a copy in `data/calendar.csv`. Rounds that are open, rolling, or announced but not yet open go into the pool and always count as matches; closed rounds move to the archive, which builds a record of when each program runs. The About tab lists rows that need an update: a round that closed with no next round, a program with no dates, or a row not checked in 90 days. Updating the calendar once a quarter keeps it current.

## Leads from incubators and water clusters

Awards like the Nicor Gas Illinois Innovator Award are posted on incubator and water-cluster websites, not on government portals. Each morning the job reads the news feeds listed in `profile.toml` under `[leads]` and keeps the posts that look like a call for startups: words like "apply", "applications open" or "call for" anywhere in the post, or "prize", "challenge", "award" or "deadline" in the title. Feeds that cover every industry must also mention water near the top. News about past winners, programs outside the US and fellowships (kept by hand in the sheet) are skipped. For newsletters that list several calls in one issue, like Climate Tech VC, the feed's `section` setting reads each item under the "Opportunities & Events" heading as its own lead.

The results go to `data/leads.csv` and the sheet's **Leads** tab, newest first, with any deadline found in the post. Nothing needs approving. Leads stay for a year. Some will be news rather than open calls, so open the link before acting on one. To add a feed, copy one of the `[[leads.feeds]]` blocks in `profile.toml`. A feed that is down only means no new leads from it that day; it doesn't fail the run.

## View it in Google Sheets

The script in [`sheet/refresh.gs`](sheet/refresh.gs) fills a **Matches** tab, a **Leads** tab and an **About** tab (sources, today's counts, how matching works) and refreshes both every day. Setup steps are at the top of the file.

For a quick read-only view instead, make a new Google Sheet and put this in cell A1. It refreshes on its own about once an hour.

```
=IMPORTDATA("https://raw.githubusercontent.com/gauravshikhargandhi-web/glia-funding-tracker/main/data/matches.csv")
```

Swap `matches.csv` for `listings.csv` to see everything. If you run your own copy, swap in your GitHub username and repository name.

## Run your own copy

1. Click **Use this template**, then **Create a new repository**, on this page. A public repository keeps GitHub Actions free.
2. Edit `profile.toml` in your copy so the keywords describe what you build.
3. Open the **Actions** tab, enable workflows if GitHub asks, choose **Daily refresh**, and click **Run workflow**.

From then on it refreshes every day at 12:00 UTC. GitHub pauses scheduled jobs on repositories with no activity for 60 days, but the daily data update counts as activity.

## Run it on your computer

Needs Python 3.11 or newer and nothing else.

```
python -m tracker.run
python -m unittest discover -s tests -t .
```
