from trustbench.agent.trace import AgentTrace, RetrievalHit
from trustbench.evals.failure_taxonomy import classify_case, is_failure, taxonomy_counts
from trustbench.evals.metrics.types import MetricResult
from trustbench.evals.runner import CaseScore, EvalRun


def cs(case_id="c", intent="refund", scores=None, hits=None):
    scores = scores or {}
    metrics = {n: MetricResult(name=n, score=s, passed=s >= 0.5) for n, s in scores.items()}
    return CaseScore(
        case_id=case_id, intent=intent, difficulty="medium", agent_text="x",
        metrics=metrics, trace=AgentTrace(ticket="t", hits=hits or []),
    )


def test_groundedness_failure_is_hallucination():
    case = cs(scores={"groundedness": 0.0})
    assert "hallucination" in classify_case(case)


def test_policy_failure_is_wrong_policy():
    case = cs(scores={"policy_adherence": 0.0})
    assert "wrong_policy" in classify_case(case)


def test_escalation_failure_tag():
    case = cs(scores={"escalation_intelligence": 0.0})
    assert "escalation_failure" in classify_case(case)


def test_tool_coverage_low_retrieval_is_retrieval_miss():
    case = cs(scores={"tool_coverage": 0.0}, hits=[RetrievalHit(doc_id="d", title="T", score=0.1)])
    assert "retrieval_miss" in classify_case(case)


def test_tool_coverage_high_retrieval_is_reasoning():
    case = cs(scores={"tool_coverage": 0.0}, hits=[RetrievalHit(doc_id="d", title="T", score=0.9)])
    assert "reasoning_failure" in classify_case(case)


def test_is_failure_true_when_key_metric_fails():
    assert is_failure(cs(scores={"resolution_accuracy": 0.0})) is True
    assert is_failure(cs(scores={"resolution_accuracy": 1.0})) is False


def test_taxonomy_counts_aggregate():
    run = EvalRun(run_label="r", agent_version="v1", cases=[
        cs("a", scores={"groundedness": 0.0}),
        cs("b", scores={"groundedness": 0.0, "policy_adherence": 0.0}),
    ])
    counts = taxonomy_counts(run)
    assert counts["hallucination"] == 2
    assert counts["wrong_policy"] == 1
