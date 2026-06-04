from trustbench.llm.groq_client import _to_messages, _to_tools
from trustbench.llm.types import Message, ToolCall, ToolResult, ToolSpec
from trustbench.retrieval.local_embedder import HashingEmbedder


def test_hashing_embedder_is_deterministic():
    e = HashingEmbedder(dim=64)
    assert e.embed(["refund my transaction"])[0] == e.embed(["refund my transaction"])[0]


def test_hashing_embedder_overlap_and_disjoint():
    e = HashingEmbedder(dim=128)
    a = e.embed(["refund my transaction"])[0]
    shared = e.embed(["transaction refund please"])[0]
    disjoint = e.embed(["zzzz qqqq wwww"])[0]
    assert sum(x * y for x, y in zip(a, shared)) > 0
    assert sum(x * y for x, y in zip(a, disjoint)) == 0


def test_to_tools_shape():
    specs = [ToolSpec(name="issue_refund", description="d", parameters={"type": "object", "properties": {}})]
    out = _to_tools(specs)
    assert out[0]["type"] == "function"
    assert out[0]["function"]["name"] == "issue_refund"


def test_to_messages_pairs_tool_call_ids():
    msgs = [
        Message(role="user", text="hi"),
        Message(role="model", tool_call=ToolCall(name="issue_refund", args={"transaction_id": "t1"})),
        Message(role="tool", tool_result=ToolResult(name="issue_refund", result={"ok": True})),
    ]
    out = _to_messages("SYS", msgs)
    assert out[0] == {"role": "system", "content": "SYS"}
    assert out[1]["role"] == "user"
    assert out[2]["role"] == "assistant"
    assert out[2]["tool_calls"][0]["function"]["name"] == "issue_refund"
    call_id = out[2]["tool_calls"][0]["id"]
    assert out[3]["role"] == "tool"
    assert out[3]["tool_call_id"] == call_id
