from __future__ import annotations

from trustbench.evals.failure_taxonomy import classify_case, is_failure
from trustbench.evals.golden import GoldenCase
from trustbench.evals.runner import EvalRun


def harvest_failures(run: EvalRun, originals: list[GoldenCase]) -> list[GoldenCase]:
    """Turn failing cases from a run into permanent regression golden cases.

    This is the simulated self-learning loop: every failure becomes a tagged golden case
    (data_source="production_sim") so the next change is tested against the exact situation
    that broke before. Mirrors the production flywheel where escalations and thumbs-down
    feed back into the eval set.
    """
    by_id = {c.case_id: c for c in originals}
    harvested: list[GoldenCase] = []
    for case in run.cases:
        if not is_failure(case):
            continue
        base = by_id.get(case.case_id)
        harvested.append(
            GoldenCase(
                case_id=f"{case.case_id}__regression",
                ticket=base.ticket if base else case.trace.ticket,
                intent=case.intent,
                difficulty=base.difficulty if base else case.difficulty,
                expected_tools=base.expected_tools if base else [],
                forbidden_tools=base.forbidden_tools if base else [],
                should_escalate=base.should_escalate if base else False,
                policy_constraints=base.policy_constraints if base else [],
                ground_truth_response=base.ground_truth_response if base else "",
                must_not_claim=base.must_not_claim if base else [],
                failure_tags=classify_case(case),
                data_source="production_sim",
                version="regressions",
                note="harvested from a failing run; keep as a permanent regression case",
            )
        )
    return harvested
