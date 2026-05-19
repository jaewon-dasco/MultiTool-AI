#!/usr/bin/env python3
"""Diagnostics handler dry-run — Temperature Min 단독 검증."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes.seed_runner_ui import run_one_seed


def main():
    seed = {"idx": 20, "name": "diag_temp_min_dryrun",
            "label": "Temperature", "value": "-25",
            "tab": "Diagnostics", "expected_kind": "diagnostics_minmax",
            "table_column": "Min"}
    r = run_one_seed(seed, label=seed["label"], value=seed["value"],
                     sidebar_tab=seed["tab"], cycle_idx=99)
    print(f"\nok: {r.get('ok')}  phase: {r.get('phase')}")
    print(f"action: {r.get('action')}")
    print(f"mt_size_delta: {r.get('mt_size_delta')}")
    vc = r.get('mt_diff', {}).get('value_changes', [])
    print(f"value_changes: {len(vc)}")
    for c in vc[:5]: print(f"  {c['tag']}: {c['old']!r} → {c['new']!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
