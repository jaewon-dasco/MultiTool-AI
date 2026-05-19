#!/usr/bin/env python3
"""io_variable_name dry-run — pin 1.2 (VAVLE_UP) → TEST_PIN2_VAR."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes.seed_runner_ui import run_one_seed


def main():
    seed = {"idx": 80, "name": "io_pin1_2_var_name_dryrun",
            "label": "1.2", "value": "TEST_PIN1_2",
            "tab": "I/O", "expected_kind": "io_variable_name",
            "connector": "1"}
    r = run_one_seed(seed, label=seed["label"], value=seed["value"],
                     sidebar_tab=seed["tab"], cycle_idx=99)
    print("\n===== RESULT =====")
    print(f"ok: {r.get('ok')}  phase: {r.get('phase')}")
    print(f"action: {r.get('action')}")
    print(f"mt_size_delta: {r.get('mt_size_delta')}")
    vc = r.get('mt_diff', {}).get('value_changes', [])
    print(f"value_changes: {len(vc)}")
    for c in vc[:8]:
        print(f"  {c['tag']}: {c['old']!r} → {c['new']!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
