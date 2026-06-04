from trustbench.agent.trace import AgentTrace
from trustbench.evals.flywheel import harvest_failures
from trustbench.evals.golden import GoldenCase
from trustbench.evals.metrics.types import MetricResult
from trustbench.evals.runner import CaseScore, EvalRun


def cs(case_id, intent, scores):
    metrics = {n: MetricResult(name=n, score=s, passed=s >= 0.5) for n, s in scores.items()}
    return CaseScore(
        case_id=case_id, intent=intent, difficulty="hard",
        agent_text="x", metrics=metrics, trace=AgentTrace(ticket=f"ticket for {case_id}"),
    )


def test_harvests_only_failures_and_tags_them():
    originals = [
        GoldenCase(case_id="a", ticket="refund crypto", intent="refund", must_not_claim=["refunded"]),
        GoldenCase(case_id="b", ticket="lost card", intent="card"),
    ]
    run = EvalRun(run_label="v2", agent_version="v2", cases=[
        cs("a", "refund", {"policy_adherence": 0.0}),
        cs("b", "card", {"resolution_accuracy": 1.0}),
    ])

    harvested = harvest_failures(run, originals)

    assert len(harvested) == 1
    new = harvested[0]
    assert new.case_id == "a__regression"
    assert new.ticket == "refund crypto"
    assert new.data_source == "production_sim"
    assert "wrong_policy" in new.failure_tags
    assert new.must_not_claim == ["refunded"]


def test_harvest_handles_case_without_original():
    run = EvalRun(run_label="v2", agent_version="v2", cases=[
        cs("orphan", "refund", {"groundedness": 0.0}),
    ])
    harvested = harvest_failures(run, originals=[])
    assert len(harvested) == 1
    assert harvested[0].ticket == "ticket for orphan"
    assert "hallucination" in harvested[0].failure_tags
