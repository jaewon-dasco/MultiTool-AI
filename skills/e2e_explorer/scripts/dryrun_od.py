#!/usr/bin/env python3
"""OD 핸들러 dry-run — Add Index, Remove, Add Sub-Index, Import 검증."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes.seed_runner_ui import run_one_seed


def run(name, action_name, label):
    seed = {"idx": 99, "name": f"{name}_dryrun", "label": label, "value": "",
            "tab": "Object Dictionary", "expected_kind": "od_toolbar", "od_action": action_name}
    r = run_one_seed(seed, label=seed["label"], value=seed["value"],
                     sidebar_tab=seed["tab"], cycle_idx=99)
    vc = r.get('mt_diff', {}).get('value_changes', [])
    print(f"  ok={r.get('ok')} action={r.get('action')} vc={len(vc)} size_delta={r.get('mt_size_delta')}")
    for c in vc[:3]: print(f"    {c['tag']}: {c['old']!r} → {c['new']!r}")


print("=== od_add_index ===")
run("od_add_index", "add_index", "Add Index")

print("\n=== od_remove ===")
run("od_remove", "remove", "Remove")

print("\n=== od_export ===")
run("od_export", "export", "Export")
