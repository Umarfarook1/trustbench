from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class GoldenCase(BaseModel):
    """One ground-truth support scenario, versioned in JSONL.

    Deterministic metrics read `expected_tools`, `forbidden_tools`, `should_escalate`,
    and `must_not_claim`. LLM-judge metrics read `ground_truth_response` and
    `policy_constraints`. `failure_tags` lets us slice known failure classes.
    """

    model_config = ConfigDict(extra="forbid")

    case_id: str
    ticket: str
    intent: str
    sub_intent: str = ""
    difficulty: str = "medium"  # easy | medium | hard | adversarial

    expected_tools: list[str] = []
    forbidden_tools: list[str] = []
    should_escalate: bool = False

    policy_constraints: list[str] = []
    ground_truth_response: str = ""
    must_not_claim: list[str] = []

    failure_tags: list[str] = []
    data_source: str = "SME_designed"  # SME_designed | production_sim | adversarial
    reviewer: str = "umar"
    version: str = "v1"
    note: str = ""


def load_golden_set(path: Path) -> list[GoldenCase]:
    """Load a JSONL golden set. Blank lines are skipped. Raises on duplicate ids."""
    cases: list[GoldenCase] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        case = GoldenCase(**json.loads(line))
        if case.case_id in seen:
            raise ValueError(f"duplicate case_id in golden set: {case.case_id}")
        seen.add(case.case_id)
        cases.append(case)
    return cases


def save_golden_set(cases: list[GoldenCase], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(c.model_dump(), ensure_ascii=False) for c in cases]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
