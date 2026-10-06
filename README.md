# GLIA Funding Tracker

A free, self-running list of open funding opportunities for water and water-adjacent startups, built for the [gener8tor Great Lakes Innovation Accelerator](https://www.gener8tor.com/greatlakes) cohort. Founders can copy it and keep it running on their own GitHub account after the program, at no cost.

Every day a GitHub job pulls public funding sources, keeps the listings that are still open, and saves them in one common format.

## What's in it

| File | What it holds |
| --- | --- |
| [`data/listings.csv`](data/listings.csv) | Every open listing from every source |
| [`data/matches.csv`](data/matches.csv) | The listings that fit [`profile.toml`](profile.toml) |
| [`data/filtered_out.csv`](data/filtered_out.csv) | Listings that fit the keywords but were removed because a startup could not bid (certification-only set-aside, construction bid, or a grant that rules out businesses), with the reason in the last column |
| [`profile.toml`](profile.toml) | Keywords and eligibility rules that decide what counts as a match |

Each row has the same columns whatever the source: title, funder, listing type, status, post and close dates, award floor and ceiling, total funding, eligibility, topics, location, link, a short summary, and the dates the tracker first and last saw it.

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
| Chicago bids posted only in the weekly PDF; City of Detroit (site blocks automated access) | Not covered | |
| [Illinois GATA](https://omb.illinois.gov/public/gata/csfa/OpportunityList.aspx) state funding opportunities | Live | No |
| [Massachusetts COMMBUYS](https://www.commbuys.com/bso/view/search/external/advancedSearchBid.xhtml?openBids=true) open bids and grants (state, cities, authorities) | Live | No |
| [Virginia eVA](https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp) open solicitations (state, universities, localities) | Live | No |
| Prize competitions: [Army xTech](https://xtech.army.mil/competitions/) and [Bureau of Reclamation](https://www.usbr.gov/research/challenges/accepting.html) | Live | No |
| Michigan EGLE (site refuses automated requests); New York state grants (no open source found yet) | Not covered | |

If one source fails on a given day, the others still update and that source keeps its previous listings. The run shows as failed in the Actions tab so you notice.

Only free, public sources are used. Sites that need a login are left out.

## View it in Google Sheets

Make a new Google Sheet and put this in cell A1. It refreshes on its own about once an hour.

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
