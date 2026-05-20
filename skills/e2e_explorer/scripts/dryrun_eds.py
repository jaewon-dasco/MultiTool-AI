#!/usr/bin/env python3
"""EDS 등록 dry-run — GC44_Epec.eds 추가."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes.seed_runner_ui import run_one_seed


def main():
    seed = {"idx": 72, "name": "net_add_slave_eds_dryrun",
            "label": "Add Slave (Generic EDS)", "value": "GC44_Epec.eds",
            "tab": None, "expected_kind": "eds_add_slave",
            "eds_path": r"C:\Program Files (x86)\Epec\MultiTool Creator 8.4\Resources\Config\SlaveDeviceTemplates\Eds\GC44_Epec.eds"}
    r = run_one_seed(seed, label=seed["label"], value=seed["value"],
                     sidebar_tab=None, cycle_idx=99)
    vc = r.get('mt_diff', {}).get('value_changes', [])
    print(f"\nok={r.get('ok')} action={r.get('action')}")
    print(f"mt_size_delta={r.get('mt_size_delta')} vc={len(vc)}")
    for c in vc[:5]: print(f"  {c['tag']}: {c['old']!r} → {c['new']!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
