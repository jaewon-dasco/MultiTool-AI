#!/usr/bin/env python3
"""PDO 핸들러 dry-run — Add Tx + Remove Tx 순차."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes.seed_runner_ui import run_one_seed


def run(seed):
    r = run_one_seed(seed, label=seed["label"], value=seed["value"],
                     sidebar_tab=seed["tab"], cycle_idx=99)
    vc = r.get('mt_diff', {}).get('value_changes', [])
    print(f"  ok={r.get('ok')} action={r.get('action')} vc={len(vc)}")
    for c in vc[:5]: print(f"    {c['tag']}: {c['old']!r} → {c['new']!r}")


# Add Tx
print("=== pdo_add_tx ===")
run({"idx": 40, "name": "pdo_add_tx", "label": "Add Tx", "value": "",
     "tab": "PDO", "expected_kind": "pdo_toolbar", "direction": "Tx", "operation": "Add"})

# Remove Tx (now there should be 3 Tx rows — added one + initial 2)
print("\n=== pdo_remove_tx ===")
run({"idx": 41, "name": "pdo_remove_tx", "label": "Remove Tx", "value": "",
     "tab": "PDO", "expected_kind": "pdo_toolbar", "direction": "Tx", "operation": "Remove"})
