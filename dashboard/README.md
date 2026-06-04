# TrustBench dashboard

A minimalist Next.js view of an eval run: the seven trust metrics overall, a per-category
heatmap, and the regression incident.

## Run

    npm install
    npm run dev        # http://localhost:3000

## Data

The dashboard reads `data/sample-run.json` and `data/sample-regression.json`, which are
illustrative data generated from the real `EvalRun` schema.

Regenerate the sample data from the repo root:

    python scripts/make_sample_dashboard_data.py

To show real numbers, run a live eval (see `../docs/RUN_LIVE.md`) and copy a results file
from `../data/results/` over `data/sample-run.json`, and a `compare_runs` output over
`data/sample-regression.json`.

## Palette

The design is intentionally minimalist. `--accent` in `app/globals.css` is a placeholder;
set it to Fini's exact brand hex (from usefini.com) for an on-brand look.

## Deploy

Deploys on Vercel as a standard Next.js app. Set the project root to `dashboard/`.
