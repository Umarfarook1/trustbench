from __future__ import annotations

from pydantic import BaseModel

from trustbench.evals.runner import CaseScore

LOW_RETRIEVAL_SCORE = 0.2


class Attribution(BaseModel):
    case_id: str
    attribution: str   # retrieval | generation | prompt | reasoning | none
    explanation: str


def _failed(case: CaseScore, name: str) -> bool:
    metric = case.metrics.get(name)
    return metric is not None and not metric.passed


def attribute(case: CaseScore) -> Attribution:
    """Walk the trace and metric outcomes to attribute a failure to one layer.

    Mirrors the decision tree in the spec: retrieval, then generation faithfulness,
    then prompt/context, then reasoning.
    """
    trace = case.trace
    top_hit = max((h.score for h in trace.hits), default=0.0)

    if _failed(case, "tool_coverage"):
        if top_hit < LOW_RETRIEVAL_SCORE:
            return Attribution(
                case_id=case.case_id,
                attribution="retrieval",
                explanation="Expected action not taken and retrieval scores were low; the right article was likely not retrieved.",
            )
        return Attribution(
            case_id=case.case_id,
            attribution="reasoning",
            explanation="Relevant articles were retrieved but the agent did not take the expected action.",
        )

    if _failed(case, "groundedness"):
        return Attribution(
            case_id=case.case_id,
            attribution="generation",
            explanation="Response made claims not supported by retrieved context or tool results; a faithfulness failure.",
        )

    if _failed(case, "policy_adherence") or _failed(case, "policy_guardrail_hard"):
        if trace.policy_in_context:
            return Attribution(
                case_id=case.case_id,
                attribution="reasoning",
                explanation="Policy was present in context but the agent misapplied it.",
            )
        return Attribution(
            case_id=case.case_id,
            attribution="prompt",
            explanation="Policy was not present in the agent context.",
        )

    if _failed(case, "escalation_intelligence"):
        return Attribution(
            case_id=case.case_id,
            attribution="reasoning",
            explanation="Agent misjudged whether the case required human escalation.",
        )

    return Attribution(
        case_id=case.case_id,
        attribution="none",
        explanation="No single dominant failure signal.",
    )
