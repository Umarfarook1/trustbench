from trustbench.agent.support_agent import AgentResult
from trustbench.agent.trace import AgentTrace, ToolSpan
from trustbench.evals.golden import GoldenCase
from trustbench.evals.metrics.deterministic import (
    escalation_intelligence,
    policy_guardrail_hard,
    tool_coverage,
)


def make_result(text: str, tool_names: list[str]) -> AgentResult:
    steps = [ToolSpan(name=n, args={}, result={}) for n in tool_names]
    trace = AgentTrace(ticket="t", steps=steps, final_response=text)
    return AgentResult(text=text, trace=trace)


def test_escalation_correct_when_expected_and_done():
    case = GoldenCase(case_id="c", ticket="t", intent="x", should_escalate=True)
    result = make_result("escalating now", ["escalate_to_human"])
    m = escalation_intelligence(case, result)
    assert m.passed is True
    assert m.score == 1.0


def test_escalation_fails_when_required_but_missing():
    case = GoldenCase(case_id="c", ticket="t", intent="x", should_escalate=True)
    result = make_result("here you go", ["issue_refund"])
    m = escalation_intelligence(case, result)
    assert m.passed is False
    assert m.score == 0.0


def test_escalation_fails_on_unwanted_escalation():
    case = GoldenCase(case_id="c", ticket="t", intent="x", should_escalate=False)
    result = make_result("ok", ["escalate_to_human"])
    assert escalation_intelligence(case, result).passed is False


def test_tool_coverage_full():
    case = GoldenCase(case_id="c", ticket="t", intent="x", expected_tools=["issue_refund"])
    result = make_result("done", ["issue_refund"])
    m = tool_coverage(case, result)
    assert m.score == 1.0
    assert m.passed is True


def test_tool_coverage_partial():
    case = GoldenCase(
        case_id="c", ticket="t", intent="x", expected_tools=["freeze_card", "escalate_to_human"]
    )
    result = make_result("done", ["freeze_card"])
    m = tool_coverage(case, result)
    assert m.score == 0.5
    assert m.passed is False


def test_tool_coverage_zero_on_forbidden():
    case = GoldenCase(
        case_id="c", ticket="t", intent="x", expected_tools=["lookup_transaction"],
        forbidden_tools=["issue_refund"],
    )
    result = make_result("done", ["lookup_transaction", "issue_refund"])
    m = tool_coverage(case, result)
    assert m.score == 0.0
    assert m.passed is False


def test_tool_coverage_is_one_when_no_expectation():
    case = GoldenCase(case_id="c", ticket="t", intent="x")
    result = make_result("just chatting", [])
    assert tool_coverage(case, result).score == 1.0


def test_policy_hard_flags_forbidden_claim():
    case = GoldenCase(
        case_id="c", ticket="t", intent="refund", must_not_claim=["refund is on the way"]
    )
    result = make_result("Good news, your refund is on the way!", [])
    m = policy_guardrail_hard(case, result)
    assert m.passed is False
    assert "claimed_forbidden" in m.detail


def test_policy_hard_flags_missed_escalation():
    case = GoldenCase(case_id="c", ticket="t", intent="x", should_escalate=True)
    result = make_result("I can handle that myself", [])
    m = policy_guardrail_hard(case, result)
    assert m.passed is False
    assert "missed_required_escalation" in m.detail


def test_policy_hard_passes_clean_case():
    case = GoldenCase(case_id="c", ticket="t", intent="x", must_not_claim=["refund issued"])
    result = make_result("Your transaction is still pending and cannot be refunded yet.", [])
    m = policy_guardrail_hard(case, result)
    assert m.passed is True
    assert m.score == 1.0
