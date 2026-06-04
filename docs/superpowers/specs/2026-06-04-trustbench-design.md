# TrustBench: a production-readiness harness for AI support agents

Design spec. Status: draft for review. Date: 2026-06-04.

Working repo name `trustbench` is a placeholder you can rename. It echoes Fini's
own "Trust Metrics" framework without putting their name on your tool.

---

## 1. Why this exists

Umar is applying for the "Founding AI Solutions Engineer (Post-Sales)" role at Fini
(usefini.com, YC S22, Amsterdam). The goal of this project is narrow and concrete:
get a call or an interview.

Two facts shape everything:

1. The job is not a pure eval-research role. It is a customer-facing, forward-deployed
   Solutions Engineer role. The person leads 3-person pods onboarding enterprise
   customers, configures agents on Zendesk and Intercom, tunes prompts and knowledge
   bases to hit 80 percent or higher resolution, writes Python scripts, and produces
   onboarding playbooks and ROI case studies. Listed comp is 100K to 175K USD, equity
   0.20 to 0.40 percent, locations Amsterdam, New York, or remote. Stated requirement
   is 3 or more years in technical customer-facing roles.

2. There is a real experience gap. Umar graduated in 2024 and does not have 3 years
   of customer-facing SE work on paper. The honest counter is that he is CTO of an AI
   startup shipping LLM systems to paying customers. The project has to carry the weight
   the resume cannot, and the outreach note has to name the gap directly.

The founders publicly emphasize agent behavior, evaluations, golden sets, reliability,
and "why did the model say what it said." Fini even open-sourced its own evaluation tool,
Paramount (`ask-fini/paramount`), and publishes a "7 Trust Metrics" framework. This
project is built to speak that exact vocabulary while also doing the customer-facing
half of the job.

## 2. The pitch sentence

Everything in this project exists to make one sentence true and provable:

> "I ran your actual playbook end to end on a realistic fintech customer: built the
> agent, hit 87 percent resolution, caught a regression that only showed up on refund
> tickets, traced it to a dropped policy clause, and wrote the 14-day onboarding plan
> and the ROI. Repo and 5-minute walkthrough inside."

That sentence is the Fini job description, already executed. That is what earns the call.

## 3. Who reads this and what convinces them

- Deepak Singla (CEO, ex-Uber). Cares about why agents behave the way they do and
  whether you can reason about it. Convinced by the judge-calibration report and the
  root-cause trace on the regression.
- Akash Tanwar (GTM lead, joined mid-2025, prolific author on the Fini blog including
  eval-themed posts). Not a technical co-founder. A good outreach target framed correctly.
  Convinced by the versioned golden set, the failure taxonomy, and the regression-by-category
  slice, packaged with a clear ROI story he could turn into a case study.
- Both are at a 14-person startup. They hire people they want in the trenches with them.
  The onboarding playbook and ROI writeup prove you can do the customer-facing work, not
  just measure it.

## 4. Goals and non-goals

Goals:
- Demonstrate the full Solutions Engineer loop on one realistic customer: configure an
  agent, evaluate it rigorously, catch and explain a regression, and package it for a
  customer with a playbook and ROI.
- Use Fini's own vocabulary (7 Trust Metrics, golden set, ground truth, regression) so
  the work reads as "already fluent in how Fini operates."
- Stay small enough that Umar can explain every component cold in an interview.

Non-goals:
- Not reproducing or attacking Fini's marketing claims (RAGless vs RAG numbers). High
  effort, low expected value, reads as adversarial.
- Not building a general-purpose eval platform. This is one scenario, done deeply.
- Not fine-tuning models. The role explicitly does not require building models.

## 5. The customer scenario

A fictional B2C fintech, a neobank we will call "Northwind" (placeholder name). It is
synthesized end to end so nothing is scraped or legally murky, and so we control the
policy depth.

Artifacts we author:
- A help center: 25 to 40 short articles (card management, transfers, KYC and identity,
  disputes and chargebacks, fees, account closure).
- A policy document: the rules an agent must obey (when a refund is allowed, when KYC
  re-verification is required, when to escalate, what the agent must never promise).
- A tool surface (mocked, deterministic): `lookup_transaction`, `issue_refund`,
  `check_kyc_status`, `pause_subscription`, `update_account_details`, `freeze_card`,
  `open_dispute`, `escalate_to_human`. Each has clear preconditions tied to the policy
  doc, so policy violations are detectable. This list is deliberate: Deepak publicly
  describes Fini's agent Sophie as one that can "issue refunds, check KYC status, pause
  subscriptions, update account details." Mirroring those exact actions makes the demo
  read as "I built a small Sophie."

Ticket data:
- Seed from the public Bitext customer-support dataset (intent-labeled, real, on
  HuggingFace), re-themed to fintech.
- Add hand-authored hard and adversarial cases: ambiguous refunds, jailbreak attempts,
  emotionally charged disputes, cases that must escalate, cases that must not.

## 6. Architecture

```
Knowledge base + policy doc ──► Ingestion ──► Retrieval index
                                                    │
User ticket ──► Support agent (Claude) ──► tool calls (mocked) ──► response + trace
                                                    │
                                          Span trace (retrieval, reasoning, tool, policy)
                                                    │
Golden set (versioned) ──► Eval harness ──► per-metric scores ──► results store (SQLite/JSONL)
                                │                                          │
                       LLM-as-judge (different provider)          Next.js dashboard (Vercel)
                                │
                       Judge calibration vs human labels
```

Data flow in one line: a ticket goes to the agent, the agent retrieves and acts and
replies while emitting a span trace, the harness scores the reply against the golden set
using deterministic checks plus an LLM judge, and results land in a store the dashboard reads.

## 7. The support agent

- Python. RAG over the Northwind knowledge base plus the mocked tool surface.
- Primary model: Gemini Flash. Cheap (generous free tier), and it makes enough mistakes
  to give a meaningful failure set to analyze. The agent is intentionally simple and
  readable, because Umar has to defend it.
- Every run emits a structured span trace: what was retrieved, what the model reasoned,
  which tools were called with what arguments, and which policy clauses were in context.
  The trace is what makes root-cause analysis possible later.
- Two agent versions will exist by design (v1 and v2) to produce the regression story.

## 8. The eval spine (the heart)

### 8.1 Golden set

- Roughly 120 cases, stored as versioned JSONL in git. Never edited in place; new
  versions are appended and old ones deprecated.
- Per-case schema: `case_id`, `turns`, `intent`, `sub_intent`, `difficulty`
  (easy/medium/hard/adversarial), `expected_tool_calls`, `policy_constraints`,
  `ground_truth_response`, `rubric` (per-dimension), `failure_tags`, `data_source`
  (production_sim / SME_designed / adversarial), `reviewer`, `version`.
- This mirrors the ground-truth concept in Fini's Paramount tool, on purpose.

### 8.2 Metrics, named after Fini's 7 Trust Metrics

| Metric | How it is measured |
| --- | --- |
| Resolution Accuracy | Deterministic outcome check plus reference-based LLM judge |
| Escalation Intelligence | Binary, vs human-labeled should-escalate ground truth, report F1 |
| Policy and Guardrail Adherence | Deterministic checks for hard rules plus LLM judge vs policy doc |
| Completeness | LLM judge that decomposes the query into sub-questions and checks each |
| Tone and Empathy | LLM judge on a 3-point rubric, validated against human labels |
| Groundedness / Hallucination | Decompose the answer into claims, verify each against retrieved context |
| Sentiment shift (optional, time-permitting) | Sentiment at first vs last turn |

Mix of deterministic and LLM-as-judge is deliberate: hard rules get hard checks, soft
qualities get judged. Umar must be able to say which is which and why.

### 8.3 LLM-as-judge done correctly

- Rubric plus chain-of-thought plus 2 few-shot examples per metric, temperature 0,
  structured output.
- The judge runs on Gemini Pro while the agent runs on Gemini Flash, a stronger model
  grading a weaker one. The real safeguard against a biased judge is not provider
  diversity, it is the calibration report in 8.4: judge-vs-human agreement is measured,
  not assumed. That measured number is the honest answer to any self-preference question.

### 8.4 Judge calibration report (the most credible artifact)

- Umar hand-labels about 30 cases.
- The harness runs the judges on those same cases and reports agreement (simple
  agreement plus Cohen's kappa), targeting 80 percent or higher.
- This proves he does not blindly trust the judge. It directly answers the founders'
  "can you reason about why the model, and the thing measuring the model, said that."

### 8.5 Failure taxonomy

Every failing case is classified into one of: hallucination, wrong policy, escalation
failure, retrieval miss, tone failure, reasoning failure, overconfidence. Drawn from the
published agentic-AI fault taxonomy. The taxonomy is a field in the schema, so failures
are sliceable.

### 8.6 Root-cause / trace attribution

For each failure, attribute it to retrieval vs generation vs reasoning vs policy using a
decision tree over the span trace:

```
Wrong answer ->
  Was the answer supported by retrieved context?
    No  -> retrieval failure
    Yes -> Did the model use the context faithfully?
             No  -> generation/faithfulness failure
             Yes -> Was the retrieved context itself wrong?
                      Yes -> knowledge-base quality issue
                      No  -> reasoning failure
```

(That tree is internal logic, not prose for the README.)

## 9. The centerpiece: a regression story

The single most JD-aligned artifact.

- Agent v1 vs agent v2. v2 improves overall resolution but silently regresses on
  billing/refund tickets, from 94 percent to 89 percent.
- Show the per-category slice so the regression is visible where the aggregate hides it.
- Run McNemar's test on the paired pass/fail outcomes so it is shown to be real, not noise.
- Root-cause it via the span traces: v2's system prompt dropped a refund-policy clause,
  so the agent stopped citing the policy on refund cases.
- Write it up as a short incident report: symptom, slice, significance, root cause, fix.

This is "drive AI agent performance" and "QA everything" from the JD, demonstrated rather
than claimed. It also speaks directly to Fini's own flagship: they shipped a "Test Suite"
product ("Era 2.0") whose pitch is catching accuracy regressions before production. The
incident report shows you already think the way their product is built.

## 10. Solutions Engineer deliverables (the customer-facing half)

- A 14-day onboarding playbook for Northwind: integration steps, knowledge-base setup,
  QA gates, escalation logic, go-live checklist. The JD names this exact deliverable.
- An ROI writeup: this configuration cuts escalation from X to Y percent, projecting Z
  dollars saved per 10,000 tickets at Fini's published 0.69 USD per resolution.
- A customer-health dashboard (Next.js on Vercel): resolution rate, CSAT proxy,
  escalation rate, plus the per-category eval breakdown and the regression view.
  Design: minimalist, using Fini's own brand palette (extracted from usefini.com during
  the dashboard phase). The point is that it looks like it could live inside Fini's
  product, not like a generic developer dashboard.

## 11. Self-learning loop (two-week polish)

Simulate Fini's improvement flywheel: take failing cases, "human-correct" them, append to
golden set v2, re-run, and show the lift. This mirrors their Chat2KB and escalation-learning
claims and shows you understand the loop, not just a one-shot eval.

## 12. External credibility anchor

Run the same harness against the public tau-bench benchmark (airline or retail) and report
numbers. This proves the harness is not hand-tuned to a toy and that you know the respected
benchmark in this space. Kept deliberately secondary so the project stays a "solutions
engineer" story, not a "researcher" story.

## 13. Tech stack and repo layout

- Python: agent, harness, scorers, traces, calibration.
- LLMs: Gemini API only. Gemini Flash for the agent, Gemini Pro for the judge. One key,
  free tier friendly.
- Storage: SQLite plus versioned JSONL in git.
- Dashboard: Next.js on Vercel (matches Umar's existing portfolio stack), minimalist,
  Fini brand palette.
- Tracing: a lightweight custom span logger so Umar can explain it, rather than a heavy
  framework.

```
trustbench/
  agent/            # the support agent, tools, retrieval
  scenario/         # Northwind KB, policy doc, tool definitions
  data/             # golden set JSONL (versioned), ticket sources
  evals/            # metrics, judges, calibration, taxonomy, root-cause
  regression/       # v1 vs v2 run + incident report
  dashboard/        # Next.js app
  playbook/         # onboarding playbook + ROI writeup
  benchmarks/       # tau-bench runner
  docs/             # this spec, the README, the Loom script
```

## 14. Two-week plan, each phase independently sendable

- Phase 1 (days 1 to 4): scenario, KB, policy, dataset, working agent with tools and
  traces. Sendable as "a working support agent."
- Phase 2 (days 5 to 8): golden set, the 7 metrics, LLM judges, calibration report.
  Sendable as "a calibrated eval harness."
- Phase 3 (days 9 to 11): regression story, failure taxonomy, root-cause traces.
  Sendable as "I caught and explained a regression."
- Phase 4 (days 12 to 14): playbook, ROI, dashboard, tau-bench anchor, README, 5-minute
  Loom, deploy, outreach note.

Ownership gate: at the end of every phase Umar writes five plain-English sentences
explaining how that piece works. If he cannot, scope is cut until he can. This is
non-negotiable because the interview tests exactly this.

## 15. Outreach plan

- Apply through the official process first.
- Then a direct note to Deepak and Akash that: names the experience gap honestly up
  front, leads with the pitch sentence, and links the repo, the Loom, and the regression
  incident report.
- Reference Fini's actual, verified public writing, not paraphrases. Strong verified
  hooks:
  - Deepak: "Companies think they've added AI to support. What they've really done is
    automate frustration." (LinkedIn, 2025)
  - Deepak: "The bottleneck in AI support isn't your model. It's your knowledge
    management." (Fini Knowledge Atlas blog)
  - Their "Test Suite" launch (catches regressions before production) is the natural
    thing to connect the regression incident report to.
- Do not use the two quotes from the original research brief (Deepak's "this is the role
  I'd want..." and Akash's "run the evals, build the golden sets..."). Neither could be
  verified in any indexed source. Quoting a founder something they did not say is a
  credibility risk.

## 16. Risks and mitigations

- Risk: over-building something Umar cannot defend. Mitigation: per-phase ownership gate,
  small readable components, custom over framework where it aids understanding.
- Risk: not finishing in two weeks. Mitigation: phase order is by decreasing send value,
  so an early stop still yields a complete artifact.
- Risk: the project reads as generic. Mitigation: Fini-specific vocabulary, the regression
  centerpiece, and the SE deliverables that match the JD line by line.
- Risk: judges are unreliable. Mitigation: the calibration report makes judge quality an
  explicit, measured thing rather than an assumption.

## 17. Success criteria

- A complete, deployed, defensible artifact that proves the pitch sentence.
- Umar can explain every component without notes.
- A sent application plus direct founder outreach.
- Leading indicator of success: a reply or a call from Fini.

## 18. Open questions

- Final product name (TrustBench is the working name unless Umar changes it).
- Whether the self-learning loop and tau-bench anchor both fit, or only one, depending on
  pace through phases 1 to 3.

Resolved:
- Models: Gemini API only (Flash for the agent, Pro for the judge).
- Dashboard: Next.js on Vercel, minimalist, Fini brand palette.
