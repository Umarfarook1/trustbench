from trustbench.agent.trace import AgentTrace, RetrievalHit, ToolSpan


def test_trace_serializes_to_dict_with_all_fields():
    trace = AgentTrace(
        ticket="I want a refund",
        agent_version="v1",
        policy_in_context=True,
        retrieval_query="I want a refund",
        hits=[RetrievalHit(doc_id="refunds", title="Refunds", score=0.91)],
        steps=[ToolSpan(name="issue_refund", args={"transaction_id": "t1"}, result={"ok": True})],
        final_response="Done, your refund is on the way.",
    )

    data = trace.model_dump()

    assert data["ticket"] == "I want a refund"
    assert data["hits"][0]["doc_id"] == "refunds"
    assert data["steps"][0]["result"]["ok"] is True
    assert data["exceeded_budget"] is False


def test_trace_defaults_are_empty():
    trace = AgentTrace(ticket="hello")
    assert trace.steps == []
    assert trace.hits == []
    assert trace.final_response == ""
