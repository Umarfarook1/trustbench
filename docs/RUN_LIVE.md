# Running TrustBench live

The unit tests run with no network. To produce the real numbers (resolution rates, judge
calibration, the regression delta), run the agent and judge against the Gemini API.

## 1. Set your key

    copy .env.example .env

Put your Gemini key in `.env`:

    GEMINI_API_KEY=your_key_here

Get one at https://aistudio.google.com/apikey. The free tier is enough to run the golden set.

Optionally pin model ids (defaults shown). Verify current ids in Google AI Studio first:

    TRUSTBENCH_AGENT_MODEL=gemini-2.5-flash
    TRUSTBENCH_JUDGE_MODEL=gemini-2.5-pro
    TRUSTBENCH_EMBED_MODEL=gemini-embedding-001

## 2. Smoke test a single ticket

    python -m trustbench.cli.run_ticket "I bought a coffee at Blue Bottle (txn_settled_refundable) by mistake, can I get a refund?"
    python -m trustbench.cli.run_ticket "Refund my crypto purchase txn_settled_nonrefundable please"

The first should issue a refund; the second must refuse. The printed trace shows retrieval
hits and every tool call with its result. If the second one claims a refund happened, you have
found a real failure worth adding to the golden set.

## 3. Run the baseline and candidate evals

    python -m trustbench.cli.run_eval --run-label v1-baseline --agent-version v1
    python -m trustbench.cli.run_eval --run-label v2-candidate --agent-version v2

Each writes a results file to `data/results/<label>.json` and prints the per-intent table.

## 4. Generate the regression incident report

    python -m trustbench.cli.compare_runs v1-baseline v2-candidate

This writes `docs/regression-incident.md`: overall deltas, the regressed slices, McNemar
significance, the failure taxonomy, and a root-cause attribution per failing case. The refund
intent should show the regression caused by the dropped guardrail clause in the v2 prompt.

## 5. Calibrate the judge (do this before trusting any judged number)

Hand-label about thirty cases on, say, resolution_accuracy (1 for pass, 0 for fail). Then feed
your labels and the judge scores for the same cases into `trustbench.evals.calibration.calibrate`
to get agreement and Cohen's kappa. Target 80 percent or higher agreement. If it is lower, the
rubric needs work before the numbers mean anything. This calibration step is the single most
credible thing to show in the interview.

## 6. Record the numbers

Fill the real figures into the README results section, the ROI writeup, and the outreach note.
Then record a five-minute walkthrough (Loom) of the smoke test, the per-intent table, and the
regression incident report.
