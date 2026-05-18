#!/usr/bin/env python3
"""Night-cycle entry point: run all UI seeds with .mtproject + .exp capture."""
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes.seed_runner_ui import run_seeds_batch, RUN_ROOT

def load_seeds(category: str = "B") -> list:
    seq_dir = ROOT / "skills" / "e2e_explorer" / "sequences_ui"
    seeds = []
    if category == "all":
        files = sorted(seq_dir.glob("*.json"))
    else:
        files = sorted(seq_dir.glob(f"{category}_*.json"))
    for fp in files:
        seeds.extend(json.load(open(fp, encoding="utf-8")))
    return seeds


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="B", help="A/B/C/D/E/F/all")
    ap.add_argument("--cycles", type=int, default=5)
    args = ap.parse_args()

    seeds = load_seeds(args.category)
    print(f"Running {len(seeds)} seeds × {args.cycles} cycles = {len(seeds)*args.cycles} executions")
    stats = run_seeds_batch(seeds, cycles=args.cycles)
    print(f"\nSTATS: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    (RUN_ROOT / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
