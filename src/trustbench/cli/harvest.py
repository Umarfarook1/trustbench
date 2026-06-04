from __future__ import annotations

import argparse
from pathlib import Path

from trustbench.config import GOLDEN_DIR, RESULTS_DIR
from trustbench.evals.flywheel import harvest_failures
from trustbench.evals.golden import load_golden_set, save_golden_set
from trustbench.evals.runner import load_run


def _resolve_run(label_or_path: str) -> Path:
    path = Path(label_or_path)
    return path if path.exists() else RESULTS_DIR / f"{label_or_path}.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Harvest failing cases from a run into permanent regression golden cases."
    )
    parser.add_argument("run", help="run label or path to a results json")
    parser.add_argument("--golden", default=str(GOLDEN_DIR / "v1.jsonl"))
    parser.add_argument("--out", default=str(GOLDEN_DIR / "regressions.jsonl"))
    args = parser.parse_args()

    run = load_run(_resolve_run(args.run))
    originals = load_golden_set(Path(args.golden))
    harvested = harvest_failures(run, originals)
    save_golden_set(harvested, Path(args.out))
    print(f"Harvested {len(harvested)} regression cases to {args.out}")


if __name__ == "__main__":
    main()
