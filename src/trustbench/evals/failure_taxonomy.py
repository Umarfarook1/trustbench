from __future__ import annotations

from collections import Counter

from trustbench.evals.runner import CaseScore, EvalRun

# The metrics that, when failing, mean the case is a failure worth classifying.
KEY_METRICS = (
    "resolution_accuracy",
    "policy_adherence",
    "policy_guardrail_hard",
    "escalation_intelligence",
    "groundedness",
)

LOW_RETRIEVAL_SCORE = 0.2


def _failed(case: CaseScore, name: str) -> bool:
    metric = case.metrics.get(name)
    return metric is not None and not metric.passed


def is_failure(case: CaseScore) -> bool:
    return any(_failed(case, m) for m in KEY_METRICS)


def classify_case(case: CaseScore) -> list[str]:
    """Map a case's failing metrics and trace into failure-class tags.

    Tags follow the published agentic-AI fault taxonomy: hallucination, wrong_policy,
    escalation_failure, retrieval_miss, reasoning_failure, tone_failure, incomplete.
    """
    tags: list[str] = []

    if _failed(case, "groundedness"):
        tags.append("hallucination")
    if _failed(case, "policy_adherence") or _failed(case, "policy_guardrail_hard"):
        tags.append("wrong_policy")
    if _failed(case, "escalation_intelligence"):
        tags.append("escalation_failure")
    if _failed(case, "tone_empathy"):
        tags.append("tone_failure")

    if _failed(case, "tool_coverage"):
        top = max((h.score for h in case.trace.hits), default=0.0)
        if top < LOW_RETRIEVAL_SCORE:
            tags.append("retrieval_miss")
        else:
            tags.append("reasoning_failure")

    if _failed(case, "completeness") and "reasoning_failure" not in tags:
        tags.append("incomplete")

    return tags


def taxonomy_counts(run: EvalRun) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for case in run.cases:
        for tag in classify_case(case):
            counter[tag] += 1
    return dict(counter)
