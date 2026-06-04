from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from pydantic import BaseModel

from trustbench.agent.support_agent import AgentResult
from trustbench.agent.trace import AgentTrace
from trustbench.evals.golden import GoldenCase
from trustbench.evals.judge import JudgeClient
from trustbench.evals.metrics.deterministic import DETERMINISTIC_METRICS
from trustbench.evals.metrics.llm_judge import JUDGE_METRICS, JudgeMetricSpec, run_judge_metric
from trustbench.evals.metrics.types import MetricResult

DeterministicMetric = Callable[[GoldenCase, AgentResult], MetricResult]


class Agent(Protocol):
    def handle(self, ticket: str) -> AgentResult:
        ...


class CaseScore(BaseModel):
    case_id: str
    intent: str
    difficulty: str
    agent_text: str
    metrics: dict[str, MetricResult]
    trace: AgentTrace


class EvalRun(BaseModel):
    run_label: str
    agent_version: str
    cases: list[CaseScore]


def run_eval(
    cases: list[GoldenCase],
    agent: Agent,
    judge: JudgeClient,
    *,
    run_label: str,
    agent_version: str = "v1",
    deterministic_metrics: list[DeterministicMetric] = DETERMINISTIC_METRICS,
    judge_specs: list[JudgeMetricSpec] = JUDGE_METRICS,
) -> EvalRun:
    scored: list[CaseScore] = []
    for case in cases:
        result = agent.handle(case.ticket)
        metrics: dict[str, MetricResult] = {}
        for metric in deterministic_metrics:
            mr = metric(case, result)
            metrics[mr.name] = mr
        for spec in judge_specs:
            mr = run_judge_metric(spec, case, result, judge)
            metrics[mr.name] = mr
        scored.append(
            CaseScore(
                case_id=case.case_id,
                intent=case.intent,
                difficulty=case.difficulty,
                agent_text=result.text,
                metrics=metrics,
                trace=result.trace,
            )
        )
    return EvalRun(run_label=run_label, agent_version=agent_version, cases=scored)


def save_run(run: EvalRun, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(run.model_dump_json(indent=2), encoding="utf-8")


def load_run(path: Path) -> EvalRun:
    return EvalRun.model_validate_json(path.read_text(encoding="utf-8"))
