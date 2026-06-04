from __future__ import annotations

import argparse
from pathlib import Path

from trustbench.config import PROJECT_ROOT, RESULTS_DIR
from trustbench.evals.failure_taxonomy import classify_case, is_failure, taxonomy_counts
from trustbench.evals.regression import compare_runs, incident_markdown
from trustbench.evals.root_cause import attribute
from trustbench.evals.runner import load_run


def _resolve(label_or_path: str) -> Path:
    path = Path(label_or_path)
    if path.exists():
        return path
    return RESULTS_DIR / f"{label_or_path}.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare two eval runs and write a regression incident report."
    )
    parser.add_argument("baseline", help="run label or path to baseline run json")
    parser.add_argument("candidate", help="run label or path to candidate run json")
    parser.add_argument("--out", default=str(PROJECT_ROOT / "docs" / "regression-incident.md"))
    args = parser.parse_args()

    baseline = load_run(_resolve(args.baseline))
    candidate = load_run(_resolve(args.candidate))
    report_obj = compare_runs(baseline, candidate)

    sections = [incident_markdown(report_obj)]

    sections.append("\n## Candidate failure taxonomy\n")
    counts = taxonomy_counts(candidate)
    if counts:
        sections.append("| Failure class | Count |\n| --- | --- |")
        for tag, count in sorted(counts.items(), key=lambda kv: -kv[1]):
            sections.append(f"| {tag} | {count} |")
    else:
        sections.append("No classified failures.")

    sections.append("\n## Root-cause attribution for candidate failures\n")
    failures = [c for c in candidate.cases if is_failure(c)]
    if failures:
        sections.append("| Case | Attribution | Explanation |\n| --- | --- | --- |")
        for case in failures:
            att = attribute(case)
            sections.append(f"| {case.case_id} | {att.attribution} | {att.explanation} |")
    else:
        sections.append("No failing cases in the candidate run.")

    markdown = "\n".join(sections)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote incident report to {out_path}\n")
    print(markdown)


if __name__ == "__main__":
    main()
