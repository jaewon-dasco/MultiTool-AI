"""diff.py — 버전 간 function_map diff 및 리포트"""

import json
from pathlib import Path


def diff_function_maps(old_path: Path, new_path: Path) -> dict:
    """두 function_map.json 비교 → {added, removed, changed} 반환"""
    old = json.loads(old_path.read_text(encoding="utf-8")) if old_path.exists() else {}
    new = json.loads(new_path.read_text(encoding="utf-8"))
    return {
        "added":   [k for k in new if k not in old],
        "removed": [k for k in old if k not in new],
        "changed": [k for k in new if k in old and new[k] != old[k]]
    }


def print_diff_report(diff: dict):
    for key in ("added", "removed", "changed"):
        items = diff.get(key, [])
        if items:
            print(f"  {key} ({len(items)}): {', '.join(items)}")
