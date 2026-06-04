from __future__ import annotations

import math

from pydantic import BaseModel

from trustbench.evals import report
from trustbench.evals.runner import CaseScore, EvalRun


class MetricDelta(BaseModel):
    metric: str
    baseline: float
    candidate: float
    delta: float


class SliceRegression(BaseModel):
    intent: str
    metric: str
    baseline: float
    candidate: float
    delta: float


class McNemarResult(BaseModel):
    metric: str
    regressed: int   # b: was pass, now fail
    improved: int    # c: was fail, now pass
    statistic: float
    p_value: float


class RegressionReport(BaseModel):
    baseline_label: str
    candidate_label: str
    overall: list[MetricDelta]
    regressed_slices: list[SliceRegression]
    mcnemar: list[McNemarResult]


def mcnemar_exact(regressed: int, improved: int) -> tuple[float, float]:
    """Continuity-corrected chi-square statistic plus an exact two-sided binomial p-value.

    `regressed` (b) = cases that passed in baseline and fail in candidate.
    `improved` (c) = cases that failed in baseline and pass in candidate.
    """
    n = regressed + improved
    if n == 0:
        return 0.0, 1.0
    statistic = (abs(regressed - improved) - 1) ** 2 / n
    k = min(regressed, improved)
    tail = sum(math.comb(n, i) for i in range(0, k + 1))
    p_value = min(1.0, 2.0 * tail * (0.5 ** n))
    return statistic, p_value


def _by_id(run: EvalRun) -> dict[str, CaseScore]:
    return {c.case_id: c for c in run.cases}


def compare_runs(
    baseline: EvalRun, candidate: EvalRun, *, slice_threshold: float = 0.05
) -> RegressionReport:
    """Diff two eval runs. Surfaces overall metric deltas, regressed per-intent slices,
    and McNemar significance on paired pass/fail outcomes over shared cases.
    """
    base_overall = report.overall_scores(baseline)
    cand_overall = report.overall_scores(candidate)
    metrics = list(base_overall.keys())

    overall = [
        MetricDelta(
            metric=m,
            baseline=base_overall[m],
            candidate=cand_overall.get(m, 0.0),
            delta=cand_overall.get(m, 0.0) - base_overall[m],
        )
        for m in metrics
    ]

    base_by_intent = report.scores_by_intent(baseline)
    cand_by_intent = report.scores_by_intent(candidate)
    regressed_slices: list[SliceRegression] = []
    for intent, base_metrics in base_by_intent.items():
        cand_metrics = cand_by_intent.get(intent, {})
        for m, base_val in base_metrics.items():
            cand_val = cand_metrics.get(m, 0.0)
            delta = cand_val - base_val
            if delta <= -slice_threshold:
                regressed_slices.append(
                    SliceRegression(
                        intent=intent, metric=m, baseline=base_val,
                        candidate=cand_val, delta=delta,
                    )
                )
    regressed_slices.sort(key=lambda s: s.delta)

    base_map = _by_id(baseline)
    cand_map = _by_id(candidate)
    shared = [cid for cid in base_map if cid in cand_map]
    mcnemar: list[McNemarResult] = []
    for m in metrics:
        b = c = 0
        for cid in shared:
            bc = base_map[cid].metrics.get(m)
            cc = cand_map[cid].metrics.get(m)
            if bc is None or cc is None:
                continue
            if bc.passed and not cc.passed:
                b += 1
            elif not bc.passed and cc.passed:
                c += 1
        stat, p = mcnemar_exact(b, c)
        mcnemar.append(McNemarResult(metric=m, regressed=b, improved=c, statistic=stat, p_value=p))

    return RegressionReport(
        baseline_label=baseline.run_label,
        candidate_label=candidate.run_label,
        overall=overall,
        regressed_slices=regressed_slices,
        mcnemar=mcnemar,
    )


def incident_markdown(report_obj: RegressionReport) -> str:
    lines = [
        f"# Regression incident: {report_obj.candidate_label} vs {report_obj.baseline_label}",
        "",
        "## Overall metric movement",
        "",
        "| Metric | Baseline | Candidate | Delta |",
        "| --- | --- | --- | --- |",
    ]
    for d in report_obj.overall:
        arrow = "down" if d.delta < 0 else ("up" if d.delta > 0 else "flat")
        lines.append(f"| {d.metric} | {d.baseline:.3f} | {d.candidate:.3f} | {d.delta:+.3f} ({arrow}) |")

    lines += ["", "## Regressed slices (intent x metric)", ""]
    if report_obj.regressed_slices:
        lines += ["| Intent | Metric | Baseline | Candidate | Delta |", "| --- | --- | --- | --- | --- |"]
        for s in report_obj.regressed_slices:
            lines.append(
                f"| {s.intent} | {s.metric} | {s.baseline:.2f} | {s.candidate:.2f} | {s.delta:+.2f} |"
            )
    else:
        lines.append("No slice regressed beyond the threshold.")

    lines += ["", "## Statistical significance (McNemar, paired pass/fail)", ""]
    lines += ["| Metric | Regressed | Improved | Statistic | p-value |", "| --- | --- | --- | --- | --- |"]
    for r in report_obj.mcnemar:
        lines.append(
            f"| {r.metric} | {r.regressed} | {r.improved} | {r.statistic:.2f} | {r.p_value:.4f} |"
        )

    return "\n".join(lines)
