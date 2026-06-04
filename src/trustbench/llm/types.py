from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]


@dataclass
class ToolResult:
    name: str
    result: dict[str, Any]


@dataclass
class ToolSpec:
    """A tool declaration handed to the model."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema object


@dataclass
class Message:
    """One turn in the agent conversation, in our own neutral form."""
    role: str  # "user", "model", or "tool"
    text: str | None = None
    tool_call: ToolCall | None = None
    tool_result: ToolResult | None = None


@dataclass
class LLMResponse:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def is_final(self) -> bool:
        return not self.tool_calls
