from __future__ import annotations

from dataclasses import dataclass

from trustbench.agent.prompts import SYSTEM_PROMPT_V1, build_system
from trustbench.agent.trace import AgentTrace, RetrievalHit, ToolSpan
from trustbench.config import MAX_AGENT_STEPS, RETRIEVAL_K
from trustbench.llm.base import LLMClient
from trustbench.llm.types import Message, ToolCall, ToolResult
from trustbench.retrieval.index import Doc, KnowledgeIndex
from trustbench.scenario.state import NorthwindState
from trustbench.scenario.tools import TOOL_SPECS, ToolRegistry


@dataclass
class AgentResult:
    text: str
    trace: AgentTrace


def format_context(hits: list[tuple[Doc, float]]) -> str:
    blocks = []
    for doc, _score in hits:
        blocks.append(f"## {doc.title}\n{doc.text}")
    return "\n\n".join(blocks)


class SupportAgent:
    def __init__(
        self,
        client: LLMClient,
        index: KnowledgeIndex,
        state: NorthwindState,
        registry: ToolRegistry,
        policy_text: str,
        system_template: str = SYSTEM_PROMPT_V1,
        version: str = "v1",
    ):
        self.client = client
        self.index = index
        self.state = state
        self.registry = registry
        self.policy_text = policy_text
        self.system_template = system_template
        self.version = version

    def handle(self, ticket: str) -> AgentResult:
        hits = self.index.search(ticket, k=RETRIEVAL_K)
        context = format_context(hits)
        system = build_system(self.system_template, self.policy_text, context)

        trace = AgentTrace(
            ticket=ticket,
            agent_version=self.version,
            policy_in_context=self.policy_text in system,
            retrieval_query=ticket,
            hits=[RetrievalHit(doc_id=d.id, title=d.title, score=s) for d, s in hits],
        )

        messages: list[Message] = [Message(role="user", text=ticket)]

        for _ in range(MAX_AGENT_STEPS):
            response = self.client.generate(system, messages, TOOL_SPECS)

            if response.is_final:
                trace.final_response = response.text or ""
                return AgentResult(text=trace.final_response, trace=trace)

            for call in response.tool_calls:
                result = self.registry.execute(call.name, self.state, call.args)
                trace.steps.append(ToolSpan(name=call.name, args=call.args, result=result))
                messages.append(Message(role="model", tool_call=ToolCall(call.name, call.args)))
                messages.append(
                    Message(role="tool", tool_result=ToolResult(name=call.name, result=result))
                )

        trace.exceeded_budget = True
        trace.final_response = "I'm escalating this to a human teammate who can help further."
        return AgentResult(text=trace.final_response, trace=trace)
