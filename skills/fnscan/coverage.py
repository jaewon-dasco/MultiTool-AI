"""coverage.py — function_map 커버리지 체크"""

import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

VERSIONS_DIR = Path(__file__).parent.parent.parent / "docs" / "versions"

# 매뉴얼 기능명 → function_map 키 alias (직접 매칭 안 될 시)
ALIASES = {
    "Configure Device":  "Configure",
    "Object Dictionary": "Configure: Object Dictionary",
    "Library Manager":   "Configure: Library Manager",
}

# UIA에 미노출되어 좌표 추정 어려운 항목 — known limitation
KNOWN_LIMITATIONS = {
    "Export Parameter CSV",  # 네트워크 hover 메뉴 (단일 디바이스 layout에 네트워크 노드 없음)
    "CANdb Export",          # 동상
    "Delete Network",        # 동상
}

MANUAL_FUNCTIONS = [
    "New Project",
    "Open Project",
    "Save Project",
    "Save As...",
    "Export Project Archive",
    "Settings",
    "System Export",
    "Export Parameter CSV",
    "CANdb Export",
    "Add Device",
    "Add Network",
    "Delete Network",
    "Configure Device",
    "Object Dictionary",
    "Library Manager",
    "Create CODESYS Project",
]


def _is_covered(fn: str, fmap: dict) -> bool:
    if fn in fmap:
        return True
    alias = ALIASES.get(fn)
    if alias and alias in fmap:
        return True
    return False


def check_coverage(ver: str) -> bool:
    """function_map.json vs MANUAL_FUNCTIONS → 90% 기준 판정 (alias·known limitation 반영)"""
    fmap_path = VERSIONS_DIR / ver / "function_map.json"
    if not fmap_path.exists():
        print(f"[ERROR] function_map.json 없음: {fmap_path}")
        return False

    fmap = json.loads(fmap_path.read_text(encoding="utf-8"))

    covered = [f for f in MANUAL_FUNCTIONS if _is_covered(f, fmap)]
    missing = [f for f in MANUAL_FUNCTIONS if not _is_covered(f, fmap)]
    blocked = [f for f in missing if f in KNOWN_LIMITATIONS]
    real_missing = [f for f in missing if f not in KNOWN_LIMITATIONS]

    achievable = len(MANUAL_FUNCTIONS) - len(blocked)
    ratio = len(covered) / achievable * 100 if achievable else 0

    print(f"커버리지: {ratio:.1f}%  ({len(covered)}/{achievable}, 달성가능 기준)")
    print(f"  전체: {len(covered)}/{len(MANUAL_FUNCTIONS)}")
    if real_missing: print(f"  누락 (실제): {real_missing}")
    if blocked:      print(f"  제외 (UIA 미노출): {blocked}")
    return ratio >= 90.0


if __name__ == "__main__":
    import sys
    ver = sys.argv[1] if len(sys.argv) > 1 else "8.4"
    ok  = check_coverage(ver)
    raise SystemExit(0 if ok else 1)
