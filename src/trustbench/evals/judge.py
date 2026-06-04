from __future__ import annotations

import json
from typing import Protocol

from pydantic import BaseModel


class JudgeVerdict(BaseModel):
    score: float  # 0.0 to 1.0
    reasoning: str = ""


class JudgeOut(BaseModel):
    """Schema the model is forced to emit."""
    score: float
    reasoning: str


class JudgeClient(Protocol):
    def judge(self, system: str, prompt: str) -> JudgeVerdict:
        ...


class GeminiJudge:
    """A stronger model (Gemini Pro) grading a weaker agent (Gemini Flash).

    Uses structured JSON output so parsing is reliable. Temperature 0 for stability.
    """

    def __init__(self, api_key: str, model: str):
        from google import genai

        self._genai = genai
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def judge(self, system: str, prompt: str) -> JudgeVerdict:
        from google.genai import types

        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=JudgeOut,
            ),
        )
        data = json.loads(response.text)
        score = float(data.get("score", 0.0))
        score = max(0.0, min(1.0, score))
        return JudgeVerdict(score=score, reasoning=str(data.get("reasoning", "")))


class FakeJudge:
    """Deterministic judge for tests. Maps substrings in the prompt to verdicts.

    Records every prompt it saw for assertions.
    """

    def __init__(
        self,
        rules: list[tuple[str, JudgeVerdict]] | None = None,
        default: JudgeVerdict | None = None,
    ):
        self._rules = rules or []
        self._default = default or JudgeVerdict(score=1.0, reasoning="default pass")
        self.prompts: list[str] = []

    def judge(self, system: str, prompt: str) -> JudgeVerdict:
        self.prompts.append(prompt)
        for needle, verdict in self._rules:
            if needle in prompt:
                return verdict
        return self._default
