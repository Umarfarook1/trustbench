from __future__ import annotations

from typing import Protocol

from trustbench.llm.types import LLMResponse, Message, ToolSpec


class LLMClient(Protocol):
    """Anything the agent can talk to: real Gemini, or a scripted fake."""

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSpec],
    ) -> LLMResponse:
        ...
