from __future__ import annotations

from google import genai

from trustbench.config import EMBED_MODEL


class GeminiEmbedder:
    def __init__(self, api_key: str, model: str = EMBED_MODEL):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.models.embed_content(model=self._model, contents=texts)
        return [list(e.values) for e in response.embeddings]
