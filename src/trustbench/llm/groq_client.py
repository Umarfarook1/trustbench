from __future__ import annotations

import json
import re
from typing import Any

from openai import BadRequestError, OpenAI

from trustbench.config import GROQ_BASE_URL
from trustbench.llm.types import LLMResponse, Message, ToolCall, ToolSpec

# Small Llama models sometimes emit a tool call in Llama's text format,
# <function=name>{json args}, which Groq rejects with code "tool_use_failed".
# We parse the intended call back out of the error so the agent loop continues.
_FUNC_RE = re.compile(r"<function=([^>\s]+)>\s*(\{.*\})", re.DOTALL)


def _recover_tool_call(err: BadRequestError) -> LLMResponse | None:
    body = getattr(err, "body", None)
    info = body.get("error", body) if isinstance(body, dict) else {}
    if not isinstance(info, dict) or info.get("code") != "tool_use_failed":
        return None
    match = _FUNC_RE.search(info.get("failed_generation", "") or "")
    if not match:
        return None
    try:
        args = json.loads(match.group(2))
    except json.JSONDecodeError:
        args = {}
    return LLMResponse(tool_calls=[ToolCall(name=match.group(1), args=args)])


def _to_tools(specs: list[ToolSpec]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": s.name,
                "description": s.description,
                "parameters": s.parameters,
            },
        }
        for s in specs
    ]


def _to_messages(system: str, messages: list[Message]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = [{"role": "system", "content": system}]
    counter = 0
    last_call_id = "call_0"
    for m in messages:
        if m.role == "user":
            out.append({"role": "user", "content": m.text or ""})
        elif m.role == "model" and m.tool_call is not None:
            counter += 1
            last_call_id = f"call_{counter}"
            out.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": last_call_id,
                            "type": "function",
                            "function": {
                                "name": m.tool_call.name,
                                "arguments": json.dumps(m.tool_call.args),
                            },
                        }
                    ],
                }
            )
        elif m.role == "tool" and m.tool_result is not None:
            out.append(
                {
                    "role": "tool",
                    "tool_call_id": last_call_id,
                    "content": json.dumps(m.tool_result.result),
                }
            )
    return out


class GroqClient:
    """Adapts Groq's OpenAI-compatible chat API to the LLMClient protocol."""

    def __init__(self, api_key: str, model: str, base_url: str = GROQ_BASE_URL):
        self._client = OpenAI(api_key=api_key, base_url=base_url, max_retries=5, timeout=60)
        self._model = model

    def generate(
        self, system: str, messages: list[Message], tools: list[ToolSpec]
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": _to_messages(system, messages),
            "temperature": 0,
        }
        specs = _to_tools(tools)
        if specs:
            kwargs["tools"] = specs
            kwargs["tool_choice"] = "auto"

        try:
            resp = self._client.chat.completions.create(**kwargs)
        except BadRequestError as e:
            recovered = _recover_tool_call(e)
            if recovered is not None:
                return recovered
            raise
        msg = resp.choices[0].message

        if msg.tool_calls:
            calls: list[ToolCall] = []
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                calls.append(ToolCall(name=tc.function.name, args=args))
            return LLMResponse(tool_calls=calls)
        return LLMResponse(text=msg.content or "")
