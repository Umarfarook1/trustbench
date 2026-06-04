from trustbench.agent.trace import AgentTrace, RetrievalHit
from trustbench.evals.metrics.types import MetricResult
from trustbench.evals.root_cause import attribute
from trustbench.evals.runner import CaseScore


def cs(scores=None, hits=None, policy_in_context=False):
    scores = scores or {}
    metrics = {n: MetricResult(name=n, score=s, passed=s >= 0.5) for n, s in scores.items()}
    return CaseScore(
        case_id="c", intent="refund", difficulty="medium", agent_text="x",
        metrics=metrics,
        trace=AgentTrace(ticket="t", hits=hits or [], policy_in_context=policy_in_context),
    )


def test_tool_coverage_fail_low_retrieval_is_retrieval():
    case = cs(scores={"tool_coverage": 0.0}, hits=[RetrievalHit(doc_id="d", title="T", score=0.05)])
    assert attribute(case).attribution == "retrieval"


def test_tool_coverage_fail_high_retrieval_is_reasoning():
    case = cs(scores={"tool_coverage": 0.0}, hits=[RetrievalHit(doc_id="d", title="T", score=0.9)])
    assert attribute(case).attribution == "reasoning"


def test_groundedness_fail_is_generation():
    case = cs(scores={"tool_coverage": 1.0, "groundedness": 0.0})
    assert attribute(case).attribution == "generation"


def test_policy_fail_with_policy_in_context_is_reasoning():
    case = cs(scores={"policy_adherence": 0.0}, policy_in_context=True)
    assert attribute(case).attribution == "reasoning"


def test_policy_fail_without_policy_in_context_is_prompt():
    case = cs(scores={"policy_adherence": 0.0}, policy_in_context=False)
    assert attribute(case).attribution == "prompt"


def test_clean_case_is_none():
    case = cs(scores={"resolution_accuracy": 1.0})
    assert attribute(case).attribution == "none"
