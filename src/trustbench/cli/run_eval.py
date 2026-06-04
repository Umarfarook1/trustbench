from __future__ import annotations

import argparse

from trustbench.cli.run_ticket import build_agent
from trustbench.config import GOLDEN_DIR, JUDGE_MODEL, RESULTS_DIR, load_api_key
from trustbench.evals.golden import load_golden_set
from trustbench.evals.judge import GeminiJudge
from trustbench.evals.report import summarize_markdown
from trustbench.evals.runner import run_eval, save_run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full eval over a golden set.")
    parser.add_argument("--golden", default=str(GOLDEN_DIR / "v1.jsonl"))
    parser.add_argument("--run-label", default="v1-baseline")
    parser.add_argument("--agent-version", default="v1")
    args = parser.parse_args()

    from pathlib import Path

    api_key = load_api_key()
    cases = load_golden_set(Path(args.golden))
    agent = build_agent(args.agent_version)
    judge = GeminiJudge(api_key, JUDGE_MODEL)

    print(f"Running {len(cases)} cases through agent {args.agent_version}, judging with {JUDGE_MODEL} ...")
    run = run_eval(cases, agent, judge, run_label=args.run_label, agent_version=args.agent_version)

    out_path = RESULTS_DIR / f"{args.run_label}.json"
    save_run(run, out_path)
    print(f"\nSaved run to {out_path}\n")
    print(summarize_markdown(run))


if __name__ == "__main__":
    main()
