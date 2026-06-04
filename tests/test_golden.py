import json

import pytest

from trustbench.config import GOLDEN_DIR
from trustbench.evals.golden import GoldenCase, load_golden_set, save_golden_set


def test_round_trip_save_and_load(tmp_path):
    cases = [
        GoldenCase(case_id="a", ticket="hi", intent="refund", expected_tools=["issue_refund"]),
        GoldenCase(case_id="b", ticket="bye", intent="card", should_escalate=True),
    ]
    path = tmp_path / "golden.jsonl"
    save_golden_set(cases, path)

    loaded = load_golden_set(path)

    assert [c.case_id for c in loaded] == ["a", "b"]
    assert loaded[0].expected_tools == ["issue_refund"]
    assert loaded[1].should_escalate is True


def test_blank_lines_are_skipped(tmp_path):
    path = tmp_path / "g.jsonl"
    path.write_text(
        json.dumps({"case_id": "a", "ticket": "x", "intent": "refund"}) + "\n\n",
        encoding="utf-8",
    )
    assert len(load_golden_set(path)) == 1


def test_duplicate_case_id_raises(tmp_path):
    path = tmp_path / "g.jsonl"
    line = json.dumps({"case_id": "dup", "ticket": "x", "intent": "refund"})
    path.write_text(line + "\n" + line + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_golden_set(path)


def test_unknown_field_is_rejected(tmp_path):
    path = tmp_path / "g.jsonl"
    path.write_text(
        json.dumps({"case_id": "a", "ticket": "x", "intent": "refund", "typo_field": 1}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception):
        load_golden_set(path)


def test_real_v1_golden_set_loads_and_is_unique():
    cases = load_golden_set(GOLDEN_DIR / "v1.jsonl")
    assert len(cases) >= 18
    ids = [c.case_id for c in cases]
    assert len(ids) == len(set(ids))
    # every case has at least one intent and a difficulty from the allowed set
    allowed = {"easy", "medium", "hard", "adversarial"}
    for c in cases:
        assert c.intent
        assert c.difficulty in allowed
