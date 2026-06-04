from trustbench.agent.support_agent import AgentResult
from trustbench.agent.trace import AgentTrace, ToolSpan
from trustbench.evals import report
from trustbench.evals.golden import GoldenCase
from trustbench.evals.judge import FakeJudge, JudgeVerdict
from trustbench.evals.runner import load_run, run_eval, save_run


class StubAgent:
    def __init__(self, text="ok", tools=None):
        self._text = text
        self._tools = tools or []

    def handle(self, ticket: str) -> AgentResult:
        steps = [ToolSpan(name=n, args={}, result={"ok": True}) for n in self._tools]
        trace = AgentTrace(ticket=ticket, steps=steps, final_response=self._text)
        return AgentResult(text=self._text, trace=trace)


def _cases():
    return [
        GoldenCase(case_id="a", ticket="refund please", intent="refund", expected_tools=["issue_refund"]),
        GoldenCase(case_id="b", ticket="lost card", intent="card", expected_tools=["freeze_card"]),
    ]


def test_run_eval_scores_all_metrics():
    agent = StubAgent(text="done", tools=["issue_refund"])
    judge = FakeJudge(default=JudgeVerdict(score=1.0, reasoning="ok"))
    run = run_eval(_cases(), agent, judge, run_label="t")
    assert len(run.cases) == 2
    names = set(run.cases[0].metrics)
    expected = {
        "escalation_intelligence", "tool_coverage", "policy_guardrail_hard",
        "resolution_accuracy", "completeness", "tone_empathy", "groundedness", "policy_adherence",
    }
    assert expected <= names


def test_report_overall_and_by_intent():
    agent = StubAgent(text="done", tools=["issue_refund"])
    judge = FakeJudge(default=JudgeVerdict(score=1.0))
    run = run_eval(_cases(), agent, judge, run_label="t")
    overall = report.overall_scores(run)
    assert overall["resolution_accuracy"] == 1.0
    by_intent = report.scores_by_intent(run)
    assert set(by_intent) == {"refund", "card"}
    md = report.summarize_markdown(run)
    assert "Eval run: t" in md


def test_save_and_load_run(tmp_path):
    agent = StubAgent()
    judge = FakeJudge(default=JudgeVerdict(score=1.0))
    run = run_eval(_cases(), agent, judge, run_label="t")
    p = tmp_path / "run.json"
    save_run(run, p)
    loaded = load_run(p)
    assert loaded.run_label == "t"
    assert len(loaded.cases) == 2
