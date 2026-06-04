from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from trustbench.retrieval.embedder import Embedder


@dataclass
class Doc:
    id: str
    title: str
    text: str


def load_knowledge_base(kb_dir: Path) -> list[Doc]:
    """Load every .md file in kb_dir into a Doc. Title is the first heading."""
    docs: list[Doc] = []
    for path in sorted(kb_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        title = path.stem
        for line in raw.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        docs.append(Doc(id=path.stem, title=title, text=raw))
    return docs


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class KnowledgeIndex:
    def __init__(self, embedder: Embedder):
        self._embedder = embedder
        self._docs: list[Doc] = []
        self._matrix: np.ndarray | None = None

    def build(self, docs: list[Doc]) -> None:
        self._docs = list(docs)
        vectors = self._embedder.embed([d.text for d in self._docs])
        self._matrix = _normalize(np.asarray(vectors, dtype=float))

    def search(self, query: str, k: int = 3) -> list[tuple[Doc, float]]:
        if self._matrix is None:
            raise RuntimeError("KnowledgeIndex.search called before build")
        q = _normalize(np.asarray(self._embedder.embed([query]), dtype=float))
        sims = self._matrix @ q[0]
        order = np.argsort(-sims)[:k]
        return [(self._docs[i], float(sims[i])) for i in order]
