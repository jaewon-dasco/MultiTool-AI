#!/usr/bin/env python3
"""Dry test 2 seeds via run_one_seed — verify full pipeline.

Seed 1: bit_rate (B/idx 01) — stable, expected OK
Seed 2: pdo_remove_rx (E/idx 43) — recent fix target
"""
import sys, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes.seed_runner_ui import run_one_seed


def log(msg): print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    # Pull seeds
    seq_dir = ROOT / "skills" / "e2e_explorer" / "sequences_ui"
    B = json.load(open(seq_dir / "B_can.json", encoding="utf-8"))
    E = json.load(open(seq_dir / "E_pdo.json", encoding="utf-8"))

    bit_rate = next(s for s in B if s["name"] == "bit_rate")
    pdo_rx = next(s for s in E if s["name"] == "pdo_remove_rx")

    log(f"Seed 1: {bit_rate['name']} idx={bit_rate['idx']} label={bit_rate['label']!r} value={bit_rate['value']!r}")
    r1 = run_one_seed(seed=bit_rate, label=bit_rate["label"],
                     value=bit_rate["value"], sidebar_tab=bit_rate.get("tab"),
                     cycle_idx=99)
    log(f"  → ok={r1.get('ok')} phase={r1.get('phase')} action={r1.get('action')}")
    if not r1.get("ok"):
        log(f"  log: {r1.get('log', [])[-3:]}")

    log("")
    log(f"Seed 2: {pdo_rx['name']} idx={pdo_rx['idx']} label={pdo_rx['label']!r}")
    r2 = run_one_seed(seed=pdo_rx, label=pdo_rx["label"],
                     value=pdo_rx["value"], sidebar_tab=pdo_rx.get("tab"),
                     cycle_idx=99)
    log(f"  → ok={r2.get('ok')} phase={r2.get('phase')} action={r2.get('action')}")
    if not r2.get("ok"):
        log(f"  log: {r2.get('log', [])[-3:]}")

    log("")
    log(f"=== Summary: bit_rate={'OK' if r1.get('ok') else 'FAIL'}  pdo_remove_rx={'OK' if r2.get('ok') else 'FAIL'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
