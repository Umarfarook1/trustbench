from __future__ import annotations

from trustbench.llm.types import LLMResponse, Message, ToolSpec


class ScriptedClient:
    """Returns pre-canned responses in order. Records every call for assertions."""

    def __init__(self, responses: list[LLMResponse]):
        self._responses = list(responses)
        self.calls: list[tuple[str, list[Message], list[ToolSpec]]] = []

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSpec],
    ) -> LLMResponse:
        self.calls.append((system, list(messages), list(tools)))
        if not self._responses:
            raise AssertionError("ScriptedClient ran out of scripted responses")
        return self._responses.pop(0)
