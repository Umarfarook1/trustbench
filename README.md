# TrustBench

A production-readiness harness for AI customer-support agents.

Most teams put a support agent in front of customers on the strength of a good demo and a
deflection rate. Neither tells you whether the agent actually resolves problems, follows
policy, or quietly got worse on one ticket category after the last prompt change.

TrustBench takes a support agent, runs it against a versioned golden set, scores it on
six trust dimensions, catches regressions by ticket category before they ship, and packages
the result with a 14-day onboarding playbook and an ROI writeup. It measures resolution, not
deflection, and it traces failures back to retrieval, generation, policy, or reasoning so you
can tell which layer actually broke. It is built around a fictional consumer neobank,
"Northwind".

It is one engineer's answer to a single question: can you prove a support agent is good
enough to put in front of real customers, and explain exactly why when it is not?

## The loop

1. A support agent ("Sophie") runs on Gemini Flash, retrieves from Northwind's knowledge base,
   and takes real actions through tools: issue refunds, check KYC, freeze cards, pause
   subscriptions, open disputes, escalate to a human.
2. Every run emits a structured trace: what was retrieved, what the model reasoned, which
   tools were called with what result, and whether policy was in context.
3. The eval harness scores each response on the six trust metrics. The soft ones use an
   LLM judge (Gemini Pro grading Gemini Flash); the hard ones are deterministic checks.
4. The judge is calibrated against human labels, so judge quality is measured, not assumed.
5. Two agent versions are compared. A regression that only shows up on one ticket category
   is surfaced, shown to be statistically significant, and traced to its root cause.

## The six trust metrics

| Trust dimension | How TrustBench measures it |
| --- | --- |
| Resolution Accuracy | LLM judge against a reference, plus deterministic tool-coverage |
| Escalation Intelligence | Deterministic: did it escalate exactly when it should have |
| Policy and Guardrail Adherence | Deterministic guardrails plus an LLM judge against the policy |
| Completeness | LLM judge: was every part of the request addressed |
| Tone and Empathy | LLM judge on a three-point rubric |
| Groundedness / Hallucination | LLM judge: is every claim supported by context or tools |

The judge always reasons before scoring, runs at temperature zero, and is validated with a
calibration report (judge-vs-human agreement and Cohen's kappa). The honest answer to "can
you trust the judge" is a measured number, not provider diversity.

## The regression centerpiece

`v2` of the agent is an "improvement" pass that makes the agent warmer and more concise. It
also silently drops one line from the system prompt: the instruction to only claim an action
happened if the tool confirms it. Overall scores can look flat or even improve, but resolution
on refund tickets drops. TrustBench:

- shows the per-intent slice where the aggregate hides the problem,
- runs McNemar's test on the paired pass/fail outcomes to show it is real, not noise,
- traces the cause back to the dropped prompt clause.

The result is a short incident report: symptom, slice, significance, root cause, fix. Generate
it with `python -m trustbench.cli.compare_runs v1-baseline v2-candidate`.

## Repo map

```
src/trustbench/
  scenario/      Northwind: knowledge base, policy, tools, seeded state
  retrieval/     embedder protocol, knowledge index, Gemini embedder
  agent/         the support agent loop, prompts (v1, v2), trace models
  llm/           neutral LLM types, client protocol, Gemini adapter, fakes
  evals/         golden set, metrics, judge, calibration, runner, regression,
                 failure taxonomy, root-cause attribution
  cli/           run_ticket, run_eval, compare_runs
data/golden/     versioned golden set (JSONL)
docs/            spec, plan, playbook, ROI, outreach, this README
dashboard/       Next.js results dashboard
```

## Setup

macOS/Linux:

    python -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    pytest                              # 82 tests, no network needed

Windows (PowerShell):

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -e ".[dev]"
    pytest                              # 82 tests, no network needed

To run live (produces the real numbers), see `docs/RUN_LIVE.md`. You need a Gemini API key.

    cp .env.example .env                # add GEMINI_API_KEY (Windows: copy .env.example .env)
    python -m trustbench.cli.run_ticket "I lost my card, what do I do?"
    python -m trustbench.cli.run_eval --run-label v1-baseline --agent-version v1
    python -m trustbench.cli.run_eval --run-label v2-candidate --agent-version v2
    python -m trustbench.cli.compare_runs v1-baseline v2-candidate

## Motivation

TrustBench was originally built to apply for the Founding AI Solutions Engineer role at Fini,
and the six trust dimensions map to Fini's published "Trust Metrics" framework. That role is
not pure eval research; it is forward-deployed solutions engineering: onboard an enterprise
customer, tune the agent to a resolution target, catch problems, and show the ROI. TrustBench
runs that entire loop end to end on one realistic customer. Fini's CEO has written that
"companies think they've added AI to support; what they've really done is automate
frustration," and that "the bottleneck in AI support isn't your model, it's your knowledge
management." TrustBench takes those claims seriously.

## Honest notes

The entire engine is unit-tested with fake LLM clients, so the test suite runs with zero API
calls. The headline numbers (resolution rate, judge calibration agreement, the size of the
refund regression) are produced when you run it live with a Gemini key; they are not
hard-coded. The regression direction is guaranteed by design because the v2 prompt change is
deliberate, but the exact figures come from the live run.
