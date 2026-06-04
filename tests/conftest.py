from __future__ import annotations

import pytest


class FakeEmbedder:
    """Deterministic bag-of-words embedder over a fixed vocabulary.

    Each text maps to a vector of token counts over `vocab`, so texts that share
    words are close in cosine space. No network, fully reproducible.
    """

    def __init__(self, vocab: list[str]):
        self.vocab = vocab

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            tokens = text.lower().split()
            vectors.append([float(tokens.count(word)) for word in self.vocab])
        return vectors


@pytest.fixture
def fake_embedder():
    vocab = [
        "refund", "refunds", "transaction", "kyc", "identity", "verification",
        "card", "freeze", "frozen", "dispute", "chargeback", "subscription",
    ]
    return FakeEmbedder(vocab)
