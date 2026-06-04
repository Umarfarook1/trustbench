"""Run the full eval live on Groq and write real results into the dashboard.

Since the Gemini project is access-denied, this runs the agent and judge on Groq
(OpenAI-compatible). Embeddings are local (Groq has none). It evaluates agent v1 and v2
over the golden set, compares them, and writes real runs into dashboard/data/.

Run: python scripts/run_live_groq.py            (all cases)
     python scripts/run_live_groq.py --limit 3  (quick smoke)
"""
from __future__ import annotations

import argparse
from pathlib import Path

from trustbench.agent.prompts import get_system_prompt
from trustbench.agent.support_agent import SupportAgent
from trustbench.config import (
    GROQ_AGENT_MODEL,
    GROQ_BASE_URL,
    GROQ_JUDGE_MODEL,
    GOLDEN_DIR,
    KB_DIR,
    POLICY_PATH,
    RESULTS_DIR,
    load_groq_key,
)
from trustbench.evals.golden import load_golden_set
from trustbench.evals.groq_judge import GroqJudge
from trustbench.evals.regression import compare_runs
from trustbench.evals.runner import run_eval, save_run
from trustbench.llm.groq_client import GroqClient
from trustbench.retrieval.index import KnowledgeIndex, load_knowledge_base
from trustbench.retrieval.local_embedder import HashingEmbedder
from trustbench.scenario.state import seed_state
from trustbench.scenario.tools import ToolRegistry

DASH = Path(__file__).resolve().parents[1] / "dashboard" / "data"


def build_agent(version: str, key: str) -> SupportAgent:
    index = KnowledgeIndex(HashingEmbedder())
    index.build(load_knowledge_base(KB_DIR))
    return SupportAgent(
        client=GroqClient(key, GROQ_AGENT_MODEL, GROQ_BASE_URL),
        index=index,
        state=seed_state(),
        registry=ToolRegistry(),
        policy_text=POLICY_PATH.read_text(encoding="utf-8"),
        system_template=get_system_prompt(version),
        version=version,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="run only the first N cases")
    args = parser.parse_args()

    key = load_groq_key()
    cases = load_golden_set(GOLDEN_DIR / "v1.jsonl")
    if args.limit:
        cases = cases[: args.limit]
    judge = GroqJudge(key, GROQ_JUDGE_MODEL, GROQ_BASE_URL)

    print(f"agent={GROQ_AGENT_MODEL}  judge={GROQ_JUDGE_MODEL}  cases={len(cases)}")

    print("running v1 ...")
    v1 = run_eval(cases, build_agent("v1", key), judge, run_label="v1-baseline", agent_version="v1")
    save_run(v1, RESULTS_DIR / "v1-baseline.json")
    print("v1 done")

    print("running v2 ...")
    v2 = run_eval(cases, build_agent("v2", key), judge, run_label="v2-candidate", agent_version="v2")
    save_run(v2, RESULTS_DIR / "v2-candidate.json")
    print("v2 done")

    reg = compare_runs(v1, v2)

    DASH.mkdir(parents=True, exist_ok=True)
    (DASH / "sample-run.json").write_text(v1.model_dump_json(indent=2), encoding="utf-8")
    (DASH / "sample-run-v2.json").write_text(v2.model_dump_json(indent=2), encoding="utf-8")
    (DASH / "sample-regression.json").write_text(reg.model_dump_json(indent=2), encoding="utf-8")
    print(f"wrote real runs into {DASH}")


if __name__ == "__main__":
    main()
