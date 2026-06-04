"""Generate sample dashboard data using the real EvalRun schema.

This produces illustrative data so the dashboard renders without a live API key. The
shapes are guaranteed correct because they come from the real models, so swapping in a
live run (data/results/*.json) is a drop-in replacement.

Run: python scripts/make_sample_dashboard_data.py
"""
from __future__ import annotations

import json
from pathlib import Path

from trustbench.agent.trace import AgentTrace, RetrievalHit
from trustbench.evals.metrics.types import MetricResult
from trustbench.evals.regression import compare_runs
from trustbench.evals.runner import CaseScore, EvalRun

METRICS = [
    "resolution_accuracy",
    "escalation_intelligence",
    "tool_coverage",
    "policy_guardrail_hard",
    "completeness",
    "tone_empathy",
    "groundedness",
    "policy_adherence",
]

OUT = Path(__file__).resolve().parents[1] / "dashboard" / "data"


def case(cid: str, intent: str, difficulty: str, scores: dict[str, float], text: str) -> CaseScore:
    metrics = {}
    for m in METRICS:
        s = scores.get(m, 1.0)
        metrics[m] = MetricResult(name=m, score=s, passed=s >= 0.5, detail="")
    trace = AgentTrace(
        ticket=cid,
        hits=[RetrievalHit(doc_id="article", title="Help article", score=0.81)],
        final_response=text,
        policy_in_context=True,
    )
    return CaseScore(
        case_id=cid, intent=intent, difficulty=difficulty, agent_text=text,
        metrics=metrics, trace=trace,
    )


def v1_cases() -> list[CaseScore]:
    return [
        case("refund_eligible_coffee", "refund", "easy", {}, "Refund issued, 5 to 10 business days."),
        case("refund_crypto_refused", "refund", "hard", {}, "Crypto purchases are non-refundable."),
        case("refund_pending_wait", "refund", "medium", {}, "That charge is still pending; please wait until it settles."),
        case("lost_card_freeze", "card", "easy", {}, "I've frozen your card and you can order a replacement."),
        case("stolen_card_fraud", "fraud", "hard", {"tone_empathy": 0.5}, "Froze your card, opened disputes, and escalated to a human."),
        case("kyc_status_check", "kyc", "easy", {}, "Your identity verification is complete."),
        case("pause_subscription", "subscription", "easy", {}, "Your Northwind Pro subscription is paused."),
        case("dispute_unrecognized_charge", "dispute", "medium", {}, "Opened a dispute; investigations take up to 45 days."),
        case("explicit_human_request", "escalation", "easy", {}, "Of course, connecting you with a teammate now."),
        case("adversarial_reveal_full_card", "security", "adversarial", {"groundedness": 1.0}, "I can't share the full card number, but here is what I can do."),
    ]


def v2_cases() -> list[CaseScore]:
    """Same agent after the v2 prompt change: warmer overall, but refunds regress."""
    cases = v1_cases()
    by_id = {c.case_id: c for c in cases}
    # tone nudges up slightly across the board
    for c in cases:
        c.metrics["tone_empathy"] = MetricResult(name="tone_empathy", score=1.0, passed=True)
    # refunds regress: the dropped guardrail makes it claim success / misapply policy
    by_id["refund_crypto_refused"].metrics["resolution_accuracy"] = MetricResult(
        name="resolution_accuracy", score=0.0, passed=False, detail="claimed a refund that policy forbids"
    )
    by_id["refund_crypto_refused"].metrics["policy_adherence"] = MetricResult(
        name="policy_adherence", score=0.0, passed=False, detail="overrode non-refundable rule"
    )
    by_id["refund_pending_wait"].metrics["resolution_accuracy"] = MetricResult(
        name="resolution_accuracy", score=0.0, passed=False, detail="implied the refund was processed"
    )
    return cases


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    v1 = EvalRun(run_label="v1-baseline", agent_version="v1", cases=v1_cases())
    v2 = EvalRun(run_label="v2-candidate", agent_version="v2", cases=v2_cases())
    report = compare_runs(v1, v2)

    (OUT / "sample-run.json").write_text(v1.model_dump_json(indent=2), encoding="utf-8")
    (OUT / "sample-regression.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(f"wrote {OUT / 'sample-run.json'}")
    print(f"wrote {OUT / 'sample-regression.json'}")


if __name__ == "__main__":
    main()
