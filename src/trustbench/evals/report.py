from __future__ import annotations

from collections import defaultdict
from statistics import mean

from trustbench.evals.runner import EvalRun


def metric_names(run: EvalRun) -> list[str]:
    names: list[str] = []
    for case in run.cases:
        for name in case.metrics:
            if name not in names:
                names.append(name)
    return names


def overall_scores(run: EvalRun) -> dict[str, float]:
    names = metric_names(run)
    out: dict[str, float] = {}
    for name in names:
        vals = [c.metrics[name].score for c in run.cases if name in c.metrics]
        out[name] = mean(vals) if vals else 0.0
    return out


def _grouped_scores(run: EvalRun, key: str) -> dict[str, dict[str, float]]:
    names = metric_names(run)
    buckets: dict[str, list] = defaultdict(list)
    for case in run.cases:
        buckets[getattr(case, key)].append(case)
    out: dict[str, dict[str, float]] = {}
    for group, cases in buckets.items():
        out[group] = {}
        for name in names:
            vals = [c.metrics[name].score for c in cases if name in c.metrics]
            out[group][name] = mean(vals) if vals else 0.0
    return out


def scores_by_intent(run: EvalRun) -> dict[str, dict[str, float]]:
    return _grouped_scores(run, "intent")


def scores_by_difficulty(run: EvalRun) -> dict[str, dict[str, float]]:
    return _grouped_scores(run, "difficulty")


def summarize_markdown(run: EvalRun) -> str:
    names = metric_names(run)
    overall = overall_scores(run)
    lines = [
        f"# Eval run: {run.run_label} (agent {run.agent_version})",
        "",
        f"Cases: {len(run.cases)}",
        "",
        "## Overall scores",
        "",
        "| Metric | Score |",
        "| --- | --- |",
    ]
    for name in names:
        lines.append(f"| {name} | {overall[name]:.3f} |")

    lines += ["", "## Scores by intent", "", "| Intent | " + " | ".join(names) + " |"]
    lines.append("| --- | " + " | ".join("---" for _ in names) + " |")
    by_intent = scores_by_intent(run)
    for intent in sorted(by_intent):
        row = " | ".join(f"{by_intent[intent][n]:.2f}" for n in names)
        lines.append(f"| {intent} | {row} |")

    return "\n".join(lines)
