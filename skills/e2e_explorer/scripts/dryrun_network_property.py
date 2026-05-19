#!/usr/bin/env python3
"""network_property 핸들러 dry-run — NETWORK1 BitRate 500 변경 단독 검증."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes.seed_runner_ui import run_one_seed


def main():
    seed = {"idx": 71, "name": "net_bitrate_change_dryrun",
            "label": "Bit Rate", "value": "500",
            "tab": None, "expected_kind": "network_property",
            "target_network": "NETWORK1"}
    r = run_one_seed(seed, label=seed["label"], value=seed["value"],
                     sidebar_tab=None, cycle_idx=99)
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
