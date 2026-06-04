from trustbench.agent.support_agent import AgentResult
from trustbench.agent.trace import AgentTrace, ToolSpan
from trustbench.evals.golden import GoldenCase
from trustbench.evals.judge import FakeJudge, JudgeVerdict
from trustbench.evals.metrics.llm_judge import (
    POLICY_ADHERENCE,
    RESOLUTION_ACCURACY,
    TONE_EMPATHY,
    render_prompt,
    run_judge_metric,
)


def make_result(text, hits=None, steps=None):
    trace = AgentTrace(ticket="t", hits=hits or [], steps=steps or [], final_response=text)
    return AgentResult(text=text, trace=trace)


def test_render_prompt_includes_reference_and_tools_for_resolution():
    case = GoldenCase(
        case_id="c", ticket="refund please", intent="refund",
        ground_truth_response="Issue refund in 5 to 10 days.",
    )
    result = make_result("done", steps=[ToolSpan(name="issue_refund", args={}, result={"ok": True})])
    prompt = render_prompt(RESOLUTION_ACCURACY, case, result)
    assert "refund please" in prompt
    assert "REFERENCE" in prompt
    assert "issue_refund" in prompt


def test_render_prompt_includes_policy_for_policy_metric():
    case = GoldenCase(
        case_id="c", ticket="x", intent="refund",
        policy_constraints=["crypto is non-refundable"],
    )
    result = make_result("no refund")
    prompt = render_prompt(POLICY_ADHERENCE, case, result)
    assert "crypto is non-refundable" in prompt


def test_run_judge_metric_maps_verdict_to_metricresult():
    case = GoldenCase(case_id="c", ticket="x", intent="refund")
    result = make_result("ok")
    judge = FakeJudge(default=JudgeVerdict(score=0.0, reasoning="bad"))
    mr = run_judge_metric(RESOLUTION_ACCURACY, case, result, judge)
    assert mr.name == "resolution_accuracy"
    assert mr.score == 0.0
    assert mr.passed is False
    assert mr.detail == "bad"


def test_fake_judge_rule_matches_on_prompt_substring():
    case = GoldenCase(case_id="c", ticket="refund my crypto", intent="refund")
    result = make_result("refund is on the way")
    judge = FakeJudge(rules=[("crypto", JudgeVerdict(score=0.0, reasoning="violated"))])
    mr = run_judge_metric(POLICY_ADHERENCE, case, result, judge)
    assert mr.passed is False
    assert "violated" in mr.detail


def test_tone_metric_passes_on_half_score():
    case = GoldenCase(case_id="c", ticket="x", intent="card")
    result = make_result("ok")
    judge = FakeJudge(default=JudgeVerdict(score=0.5, reasoning="acceptable"))
    mr = run_judge_metric(TONE_EMPATHY, case, result, judge)
    assert mr.score == 0.5
    assert mr.passed is True  # threshold 0.5
