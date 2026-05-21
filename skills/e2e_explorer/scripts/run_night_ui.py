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
    ap.add_argument("--legacy", action="store_true",
                    help="모든 시드를 매 cycle 반복 (이전 동작). 기본은 adaptive 모드.")
    args = ap.parse_args()

    seeds = load_seeds(args.category)
    mode = "legacy (모든 시드×cycles 반복)" if args.legacy else "adaptive (cycle 0 전체 + 이후 fail만)"
    print(f"Mode: {mode}")
    print(f"Seeds: {len(seeds)}, max cycles: {args.cycles}")
    if not args.legacy:
        print(f"Adaptive 예상: 1회차 {len(seeds)} + 이후 fail만 재실행 (최대 {len(seeds)*args.cycles})")
    else:
        print(f"Legacy 총 {len(seeds)*args.cycles} executions")
    stats = run_seeds_batch(seeds, cycles=args.cycles, adaptive=(not args.legacy))
    print(f"\nSTATS: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    (RUN_ROOT / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
