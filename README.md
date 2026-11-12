# Odisha Tender Desk – website

Static, SEO-first site of open Odisha civil tenders with BOQ breakdowns and market statistics.
Live: https://clearkart1-a11y.github.io/odisha-tender-desk/

## How it runs by itself
`.github/workflows/site.yml` runs twice a day (06:10 and 18:10 IST):
1. `tools/collect_open.py` reads the public "Tenders by Organisation" pages on tendersodisha.gov.in (no captcha),
   adds new tenders and refreshes dates in `data/active.json.gz`, and commits the change.
2. `tools/site_gen.py` rebuilds every page, the sitemap and robots.txt.
3. The site is deployed to GitHub Pages.

If the portal is down, the build still deploys the last good data. Any push to `main` also rebuilds.

## Data (`data/`, gzipped JSON, no bidder names)
| File | What | Updated |
|---|---|---|
| active.json.gz | Open and recently closed tenders (detail fields + document list) | automatically |
| results_2026.json.gz | 2026 results: winning-bid % and bidder count per tender (no names) | manually (results need a captcha) |
| boq_summary.json.gz | Per tender: BOQ item count, items making 80% of value, top 6 items | manually (BOQ zips need a captcha) |
| boq_mix.json.gz | Per tender BOQ cost mix and work class | manually |

Bidder-level data (names, profiles, rival pairs) is deliberately not in this public repo.

## Run locally
```
pip install -r requirements.txt
python tools/collect_open.py      # optional: refresh tenders
python tools/site_gen.py          # builds ./_site
```
Env: `SITE_URL` (canonical root), `BASE` (path prefix for a project site, e.g. /odisha-tender-desk; empty on a custom domain), `FORM_ENDPOINT` (sign-up form target).

## Moving to a custom domain
Add a `CNAME` step or file, set `SITE_URL=https://yourdomain` and `BASE=` (empty) in the workflow.
