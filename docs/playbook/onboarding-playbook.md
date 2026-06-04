# Northwind onboarding playbook (14 days to live)

This is the playbook a Solutions Engineer would follow to take a new customer, "Northwind"
(a consumer neobank), from kickoff to an autonomous support agent hitting an 80 percent or
higher resolution rate. It mirrors the real deployment loop: ingest knowledge, configure
tools and policy, evaluate, fix by category, and gate go-live on measured quality.

The phases below map one to one to TrustBench modules, so every step is something you can run
and show, not just describe.

## Day 0 to 2: Discovery and knowledge

Goal: understand the support surface and make the knowledge AI-ready.

- Inventory the top ticket intents with the customer (refunds, KYC, card issues, disputes,
  subscriptions, account changes). For Northwind these became the `intent` taxonomy in the
  golden set.
- Ingest the help center and policy into a structured knowledge layer. In TrustBench the
  knowledge base is `src/trustbench/scenario/knowledge_base/` and the binding rules live in
  `policy.md`. The rule a senior engineer cares about: the policy document is the single
  source of truth the agent and the judge both read.
- Identify which actions the agent must be able to take, and confirm each maps to a real,
  permissioned API. Northwind's tool surface mirrors the actions Fini's agent takes: issue
  refunds, check KYC, pause subscriptions, update account details, freeze cards, open
  disputes, escalate.

Exit check: every top intent has at least one knowledge article and a clear policy rule.

## Day 2 to 5: Configure the agent

Goal: a working agent that retrieves and acts.

- Wire retrieval over the knowledge base and connect the tools with their preconditions. A
  refund tool that silently succeeds on a non-refundable charge is a latent incident; in
  TrustBench `issue_refund` returns a structured `ok: false` with a reason, so the failure is
  inspectable.
- Write the system prompt against the policy. Keep the guardrails explicit (only claim an
  action happened if the tool confirms it). This single clause is the one the v2 regression
  later removes, which is exactly why it belongs in the prompt and in review.
- Smoke test with `python -m trustbench.cli.run_ticket "..."` across a handful of real-looking
  tickets, including one that must be refused.

Exit check: the agent resolves an easy ticket end to end and refuses an out-of-policy one.

## Day 5 to 9: Build the golden set and evaluate

Goal: turn "it seems to work" into a number.

- Build a golden set of benchmark conversations with the customer's domain experts. Each case
  carries the ticket, expected tools, whether it should escalate, the policy in play, a
  reference resolution, and forbidden claims. This is `data/golden/v1.jsonl`.
- Run the full eval: `python -m trustbench.cli.run_eval --run-label v1-baseline`. This scores
  every case on the seven trust metrics and slices the results by intent.
- Calibrate the judge. Hand-label about thirty cases, then compare the LLM judge to your
  labels and confirm 80 percent or higher agreement before trusting any judged number. The
  math is in `trustbench.evals.calibration`.

Exit check: a baseline score per metric per intent, and a calibrated judge.

## Day 9 to 12: Fix by category and protect against regressions

Goal: raise the weak intents without breaking the strong ones.

- Read the per-intent table. Fix the lowest intents first: a retrieval miss is a knowledge
  fix, a reasoning failure is a prompt fix, a policy failure is a guardrail fix. The
  root-cause attribution in `trustbench.evals.root_cause` tells you which.
- After every change, re-run the eval and compare against the baseline with
  `compare_runs`. Block any change that regresses a slice, even if the overall number improves.
  This is the discipline that separates a 95 percent agent from a 70 percent plateau.

Exit check: no intent below the agreed threshold, and no regressed slice versus baseline.

## Day 12 to 14: Go-live gate and handover

Goal: ship with evidence, and leave the customer able to keep improving.

- Confirm the go-live criteria are met: overall resolution at or above target, escalation
  intelligence near perfect on the sensitive intents, zero hard guardrail violations.
- Stand up the customer-health view (the dashboard) showing resolution rate, escalation rate,
  and the per-intent breakdown.
- Hand over the self-learning loop: production escalations and thumbs-down become new golden
  cases, which become regression tests, which protect the next change. The loop is what keeps
  the agent improving after you leave.

Exit check: go-live criteria met and signed off, dashboard live, feedback loop documented.

## Why this is gated, not vibes

Every transition above is a measured check, not a feeling. That is the whole point: an
enterprise will not trust an agent because it demos well. It trusts it because someone can show
the resolution number, the calibrated judge behind that number, and the regression tests that
keep it from sliding.
