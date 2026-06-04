from __future__ import annotations

import json

from openai import OpenAI

from trustbench.config import GROQ_BASE_URL
from trustbench.evals.judge import JudgeVerdict

_JSON_INSTRUCTION = (
    ' Respond with ONLY a JSON object of the form {"score": <number 0.0 to 1.0>, '
    '"reasoning": <short string>}.'
)


class GroqJudge:
    """A judge on Groq using JSON mode. A different model family than the agent, so it is
    not grading its own outputs."""

    def __init__(self, api_key: str, model: str, base_url: str = GROQ_BASE_URL):
        self._client = OpenAI(api_key=api_key, base_url=base_url, max_retries=5, timeout=60)
        self._model = model

    def judge(self, system: str, prompt: str) -> JudgeVerdict:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system + _JSON_INSTRUCTION},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = {}
        try:
            score = float(data.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        score = max(0.0, min(1.0, score))
        return JudgeVerdict(score=score, reasoning=str(data.get("reasoning", ""))[:300])
