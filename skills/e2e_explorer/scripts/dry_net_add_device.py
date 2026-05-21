#!/usr/bin/env python3
"""Dry test: net_add_device only — verify 4b52075 fix (Device column x + bidirectional match)."""
import sys, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes.seed_runner_ui import run_one_seed


def log(msg): print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    seq = json.load(open(ROOT / "skills/e2e_explorer/sequences_ui/A_network.json", encoding="utf-8"))
    seed = next(s for s in seq if s["name"] == "net_add_device")
    log(f"Seed: {seed['name']} idx={seed['idx']} dialog={seed.get('dialog')}")

    r = run_one_seed(seed=seed, label=seed["label"], value=seed["value"],
                     sidebar_tab=seed.get("tab"), cycle_idx=99)
    log(f"→ ok={r.get('ok')} phase={r.get('phase')} action={r.get('action')}")
    log(f"  log: {r.get('log',[])[-5:]}")
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
