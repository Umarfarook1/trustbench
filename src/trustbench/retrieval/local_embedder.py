from __future__ import annotations

import hashlib
import re


class HashingEmbedder:
    """A deterministic, no-API bag-of-words embedder via feature hashing.

    Used for the Groq path, since Groq has no embeddings endpoint. The knowledge base is
    tiny (a handful of articles), so hashed lexical overlap routes a query to the right
    article reliably and reproducibly, with zero network calls.
    """

    def __init__(self, dim: int = 512):
        self.dim = dim

    def _vec(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in re.findall(r"[a-z0-9]+", text.lower()):
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16) % self.dim
            vec[h] += 1.0
        return vec

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]
