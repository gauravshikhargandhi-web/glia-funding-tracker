# GLIA Funding Tracker

A free, self-running list of open funding opportunities for water and water-adjacent startups, built for the [gener8tor Great Lakes Innovation Accelerator](https://www.gener8tor.com/greatlakes) cohort. Founders can copy it and keep it running on their own GitHub account after the program, at no cost.

Every day a GitHub job pulls public funding sources, keeps the listings that are still open, and saves them in one common format.

## What's in it

| File | What it holds |
| --- | --- |
| [`data/listings.csv`](data/listings.csv) | Every open listing from every source |
| [`data/matches.csv`](data/matches.csv) | The listings that fit [`profile.toml`](profile.toml) |
| [`profile.toml`](profile.toml) | Keywords and eligibility rules that decide what counts as a match |

Each row has the same columns whatever the source: title, funder, listing type, status, post and close dates, award floor and ceiling, total funding, eligibility, topics, location, link, a short summary, and the dates the tracker first and last saw it.

## Sources

| Source | Status | Key needed |
| --- | --- | --- |
| [Grants.gov](https://www.grants.gov) daily extract (all federal grants and forecasts) | Live | No |
| [California Grants Portal](https://data.ca.gov/dataset/california-grants-portal) (all California state grants and loans) | Live | No |
| [NYC City Record Online](https://a856-cityrecord.nyc.gov/) solicitations | Live | No |
| SAM.gov contract opportunities | Planned | Free personal key |
| Federal Register notices | Planned | No |
| Chicago and Detroit bid pages | Planned | No |
| Other state grant portals (IL, MA, MI, NY, VA) | Planned | No |

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
