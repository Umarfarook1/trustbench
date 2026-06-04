from trustbench.agent.trace import AgentTrace
from trustbench.evals.metrics.types import MetricResult
from trustbench.evals.regression import compare_runs, incident_markdown, mcnemar_exact
from trustbench.evals.runner import CaseScore, EvalRun


def cs(case_id, intent, scores):
    metrics = {n: MetricResult(name=n, score=s, passed=s >= 0.5) for n, s in scores.items()}
    return CaseScore(
        case_id=case_id, intent=intent, difficulty="medium",
        agent_text="x", metrics=metrics, trace=AgentTrace(ticket="t"),
    )


def test_mcnemar_no_discordant_pairs():
    stat, p = mcnemar_exact(0, 0)
    assert stat == 0.0
    assert p == 1.0


def test_mcnemar_exact_p_value():
    # 5 regressions, 0 improvements: two-sided exact p = 2 * 1 * 0.5^5 = 0.0625
    _stat, p = mcnemar_exact(5, 0)
    assert abs(p - 0.0625) < 1e-9


def test_mcnemar_symmetric():
    assert mcnemar_exact(5, 0)[1] == mcnemar_exact(0, 5)[1]


def _runs():
    baseline = EvalRun(run_label="v1", agent_version="v1", cases=[
        cs("r1", "refund", {"resolution_accuracy": 1.0}),
        cs("r2", "refund", {"resolution_accuracy": 1.0}),
        cs("c1", "card", {"resolution_accuracy": 1.0}),
    ])
    candidate = EvalRun(run_label="v2", agent_version="v2", cases=[
        cs("r1", "refund", {"resolution_accuracy": 0.0}),
        cs("r2", "refund", {"resolution_accuracy": 0.0}),
        cs("c1", "card", {"resolution_accuracy": 1.0}),
    ])
    return baseline, candidate


def test_compare_runs_overall_delta_negative():
    baseline, candidate = _runs()
    rep = compare_runs(baseline, candidate)
    res = next(d for d in rep.overall if d.metric == "resolution_accuracy")
    assert res.delta < 0
    assert abs(res.baseline - 1.0) < 1e-9


def test_compare_runs_flags_refund_slice():
    baseline, candidate = _runs()
    rep = compare_runs(baseline, candidate)
    refund_regressions = [s for s in rep.regressed_slices if s.intent == "refund"]
    assert refund_regressions
    assert refund_regressions[0].metric == "resolution_accuracy"
    # the card slice did not regress
    assert all(s.intent != "card" for s in rep.regressed_slices)


def test_compare_runs_mcnemar_counts_regressions():
    baseline, candidate = _runs()
    rep = compare_runs(baseline, candidate)
    res = next(m for m in rep.mcnemar if m.metric == "resolution_accuracy")
    assert res.regressed == 2
    assert res.improved == 0


def test_incident_markdown_renders():
    baseline, candidate = _runs()
    rep = compare_runs(baseline, candidate)
    md = incident_markdown(rep)
    assert "Regression incident" in md
    assert "resolution_accuracy" in md
