from __future__ import annotations

from google import genai
from google.genai import types

from trustbench.llm.types import LLMResponse, Message, ToolCall, ToolSpec


def _to_tools(specs: list[ToolSpec]) -> list[types.Tool]:
    declarations = [
        types.FunctionDeclaration(
            name=s.name,
            description=s.description,
            parameters_json_schema=s.parameters,
        )
        for s in specs
    ]
    return [types.Tool(function_declarations=declarations)]


def _to_contents(messages: list[Message]) -> list[types.Content]:
    contents: list[types.Content] = []
    for m in messages:
        if m.role == "user":
            contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=m.text or "")])
            )
        elif m.role == "model" and m.tool_call is not None:
            contents.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            function_call=types.FunctionCall(
                                name=m.tool_call.name, args=m.tool_call.args
                            )
                        )
                    ],
                )
            )
        elif m.role == "tool" and m.tool_result is not None:
            contents.append(
                types.Content(
                    role="tool",
                    parts=[
                        types.Part.from_function_response(
                            name=m.tool_result.name, response=m.tool_result.result
                        )
                    ],
                )
            )
    return contents


class GeminiClient:
    """Adapts the google-genai SDK to the LLMClient protocol."""

    def __init__(self, api_key: str, model: str):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSpec],
    ) -> LLMResponse:
        response = self._client.models.generate_content(
            model=self._model,
            contents=_to_contents(messages),
            config=types.GenerateContentConfig(
                system_instruction=system,
                tools=_to_tools(tools),
                temperature=0.0,
            ),
        )

        function_calls = response.function_calls or []
        if function_calls:
            return LLMResponse(
                tool_calls=[
                    ToolCall(name=fc.name, args=dict(fc.args or {})) for fc in function_calls
                ]
            )
        return LLMResponse(text=response.text or "")
