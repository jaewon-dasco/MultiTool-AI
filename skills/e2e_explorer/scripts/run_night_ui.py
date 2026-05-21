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
                    help="모든 시드를 매 cycle 반복 (Phase 1 batch 건너뜀, 이전 동작).")
    args = ap.parse_args()

    seeds = load_seeds(args.category)
    if args.legacy:
        print(f"Mode: legacy (모든 시드×cycles 반복)")
        print(f"Seeds: {len(seeds)}, cycles: {args.cycles}, total: {len(seeds)*args.cycles}")
    else:
        from skills.e2e_explorer.recipes.verified_store import split_by_verified
        bs, iso = split_by_verified(seeds)
        print(f"Mode: Phase 1 batch + Phase 2 isolated")
        print(f"Phase 1: {len(bs)} verified seeds (batch, 1 session, 1 save, 1 export)")
        print(f"Phase 2: {len(iso)} unverified seeds × up to {args.cycles} isolated cycles")
    stats = run_seeds_batch(seeds, cycles=args.cycles, legacy=args.legacy)
    print(f"\nSTATS: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    (RUN_ROOT / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
