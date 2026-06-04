from trustbench.agent.prompts import SYSTEM_PROMPT_V1, build_system
from trustbench.agent.support_agent import SupportAgent, format_context
from trustbench.agent.trace import AgentTrace
from trustbench.llm.fakes import ScriptedClient
from trustbench.llm.types import LLMResponse, ToolCall
from trustbench.retrieval.index import Doc, KnowledgeIndex
from trustbench.scenario.state import seed_state
from trustbench.scenario.tools import ToolRegistry


def test_llmresponse_is_final_when_no_tool_calls():
    resp = LLMResponse(text="Hi there")
    assert resp.is_final is True


def test_llmresponse_not_final_when_tool_calls_present():
    resp = LLMResponse(tool_calls=[ToolCall(name="issue_refund", args={"transaction_id": "t1"})])
    assert resp.is_final is False
    assert resp.text is None


def test_build_system_injects_policy_and_context():
    out = build_system(SYSTEM_PROMPT_V1, policy="POLICY-TEXT", context="CONTEXT-TEXT")
    assert "POLICY-TEXT" in out
    assert "CONTEXT-TEXT" in out
    assert "[[POLICY]]" not in out
    assert "[[CONTEXT]]" not in out


def _index(fake_embedder):
    docs = [
        Doc(id="refunds", title="Refunds", text="refund refunds transaction"),
        Doc(id="kyc", title="KYC", text="kyc identity verification"),
    ]
    index = KnowledgeIndex(fake_embedder)
    index.build(docs)
    return index


def _agent(client, fake_embedder):
    return SupportAgent(
        client=client,
        index=_index(fake_embedder),
        state=seed_state(),
        registry=ToolRegistry(),
        policy_text="POLICY",
        version="v1",
    )


def test_agent_returns_text_directly_when_model_replies(fake_embedder):
    client = ScriptedClient([LLMResponse(text="Hello, how can I help?")])
    agent = _agent(client, fake_embedder)

    result = agent.handle("hi")

    assert result.text == "Hello, how can I help?"
    assert isinstance(result.trace, AgentTrace)
    assert result.trace.steps == []
    assert result.trace.policy_in_context is True
    assert result.trace.hits  # retrieval ran


def test_agent_executes_tool_then_replies(fake_embedder):
    client = ScriptedClient([
        LLMResponse(tool_calls=[ToolCall(name="issue_refund", args={"transaction_id": "txn_settled_refundable"})]),
        LLMResponse(text="Your refund is on the way."),
    ])
    agent = _agent(client, fake_embedder)

    result = agent.handle("refund my coffee please")

    assert result.text == "Your refund is on the way."
    assert len(result.trace.steps) == 1
    assert result.trace.steps[0].name == "issue_refund"
    assert result.trace.steps[0].result["ok"] is True
    # the tool result was fed back to the model on the second call
    assert len(client.calls) == 2


def test_agent_records_failed_tool_result(fake_embedder):
    client = ScriptedClient([
        LLMResponse(tool_calls=[ToolCall(name="issue_refund", args={"transaction_id": "txn_settled_nonrefundable"})]),
        LLMResponse(text="I cannot refund that, it is non-refundable."),
    ])
    agent = _agent(client, fake_embedder)

    result = agent.handle("refund my crypto purchase")

    assert result.trace.steps[0].result["ok"] is False
    assert result.trace.steps[0].result["reason"] == "not_refundable_per_policy"


def test_agent_stops_at_step_budget(fake_embedder):
    # model always asks for another tool call, never replies
    looping = [
        LLMResponse(tool_calls=[ToolCall(name="lookup_transaction", args={"transaction_id": "txn_pending"})])
        for _ in range(50)
    ]
    client = ScriptedClient(looping)
    agent = _agent(client, fake_embedder)

    result = agent.handle("loop forever")

    assert result.trace.exceeded_budget is True
    assert "escalat" in result.text.lower()


def test_format_context_includes_titles():
    docs = [(Doc(id="refunds", title="Refunds", text="body text here"), 0.9)]
    out = format_context(docs)
    assert "Refunds" in out
    assert "body text here" in out
