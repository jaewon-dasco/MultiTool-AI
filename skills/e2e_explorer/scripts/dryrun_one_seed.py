#!/usr/bin/env python3
"""1 시드 dry-run — 새 clean baseline의 노이즈 감소 검증.

기본 시드: application_node_id (numeric, 안정적 작동 검증됨).
출력: value_changes 개수 (이전 28 → 목표 1).
"""
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes.seed_runner_ui import run_one_seed


def main():
    # B_can.json의 application_node_id 시드
    seed = {"idx": 2, "name": "application_node_id_dryrun", "label": "Application Node-ID",
            "value": "5", "tab": "CAN", "expected_kind": "numeric_or_text"}
    r = run_one_seed(seed, label=seed["label"], value=seed["value"],
                     sidebar_tab=seed["tab"], cycle_idx=99)
    print("\n===== RESULT =====")
    print(f"ok: {r.get('ok')}  phase: {r.get('phase')}")
    print(f"mt_size_delta: {r.get('mt_size_delta')}")
    vc = r.get('mt_diff', {}).get('value_changes', [])
    print(f"value_changes: {len(vc)}")
    for c in vc[:5]:
        print(f"  {c['tag']}: {c['old']!r} → {c['new']!r}")
    print(f"\\n📊 노이즈 평가: {len(vc)} (이전 28건 vs 목표 1건)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
