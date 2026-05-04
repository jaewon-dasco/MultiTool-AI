"""coverage.py — function_map 커버리지 체크"""

import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

VERSIONS_DIR = Path(__file__).parent.parent.parent / "docs" / "versions"

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


def check_coverage(ver: str) -> bool:
    """function_map.json vs MANUAL_FUNCTIONS → 90% 기준 판정"""
    fmap_path = VERSIONS_DIR / ver / "function_map.json"
    if not fmap_path.exists():
        print(f"[ERROR] function_map.json 없음: {fmap_path}")
        return False

    fmap    = json.loads(fmap_path.read_text(encoding="utf-8"))
    missing = [f for f in MANUAL_FUNCTIONS if f not in fmap]
    ratio   = (len(MANUAL_FUNCTIONS) - len(missing)) / len(MANUAL_FUNCTIONS) * 100

    print(f"커버리지: {ratio:.1f}%  ({len(MANUAL_FUNCTIONS) - len(missing)}/{len(MANUAL_FUNCTIONS)})")
    if missing:
        print(f"누락: {missing}")
    return ratio >= 90.0


if __name__ == "__main__":
    import sys
    ver = sys.argv[1] if len(sys.argv) > 1 else "8.4"
    ok  = check_coverage(ver)
    raise SystemExit(0 if ok else 1)
