"""expscan/run.py — .exp 생성 패턴 분석 v1

서브명령:
  capture <label>                  현재 .exp 를 label.exp 로 저장
  diff    <baseline> <variant>     두 캡처 비교 → variant.diff 생성
  mapping <variant> [설명]         mapping.json 갱신
  list                             캡처·diff 목록

워크플로:
  1) MultiTool에서 baseline 상태 → PROJECT > System Export (Ctrl+Alt+E)
  2) py skills/expscan/run.py capture baseline
  3) MultiTool에서 단일 설정 변경 → System Export 재실행
  4) py skills/expscan/run.py capture variant_X
  5) py skills/expscan/run.py diff baseline variant_X
  6) py skills/expscan/run.py mapping variant_X "Bitrate 250→500"

생성 경로: {ProjectRoot}/{DeviceName}/{DeviceName}.exp (System Export가 덮어씀)
"""

import hashlib
import json
import shutil
import sys
from difflib import unified_diff
from pathlib import Path

ROOT     = Path(__file__).parent.parent.parent
EXP_FILE = ROOT / "DemoProject" / "ScanDemo" / "EPEC_CU1" / "EPEC_CU1.exp"
PATTERNS = ROOT / "docs" / "exp_patterns"


def cmd_capture(label: str) -> int:
    if not EXP_FILE.exists():
        print(f"[ERROR] exp 파일 없음: {EXP_FILE}")
        return 1
    PATTERNS.mkdir(parents=True, exist_ok=True)
    dst    = PATTERNS / f"{label}.exp"
    shutil.copy(EXP_FILE, dst)
    text   = dst.read_text(encoding="utf-8", errors="replace")
    digest = hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()[:12]
    lines  = text.count("\n") + (0 if text.endswith("\n") else 1)
    print(f"  captured: {dst.relative_to(ROOT)}")
    print(f"  lines:    {lines}")
    print(f"  md5:      {digest}")
    return 0


def cmd_diff(baseline: str, variant: str) -> int:
    a_path = PATTERNS / f"{baseline}.exp"
    b_path = PATTERNS / f"{variant}.exp"
    for p in (a_path, b_path):
        if not p.exists():
            print(f"[ERROR] 파일 없음: {p}")
            return 1
    a = a_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    b = b_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    diff_text = "".join(unified_diff(
        a, b, fromfile=a_path.name, tofile=b_path.name, lineterm="\n"
    ))
    if not diff_text:
        print(f"  diff: 0 lines (동일)")
        return 0
    out = PATTERNS / f"{variant}.diff"
    out.write_text(diff_text, encoding="utf-8")
    added   = sum(1 for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff_text.splitlines() if l.startswith("-") and not l.startswith("---"))
    print(f"  diff: +{added} -{removed} → {out.relative_to(ROOT)}")
    return 0


def cmd_mapping(variant: str, description: str) -> int:
    diff_path = PATTERNS / f"{variant}.diff"
    exp_path  = PATTERNS / f"{variant}.exp"
    map_path  = PATTERNS / "mapping.json"
    if not diff_path.exists():
        print(f"[ERROR] {diff_path} 없음 — 먼저 diff 실행")
        return 1
    mapping = {}
    if map_path.exists():
        mapping = json.loads(map_path.read_text(encoding="utf-8"))
    diff_text = diff_path.read_text(encoding="utf-8")
    added   = sum(1 for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff_text.splitlines() if l.startswith("-") and not l.startswith("---"))
    mapping[variant] = {
        "description": description,
        "exp_file":    str(exp_path.relative_to(ROOT)).replace("\\", "/"),
        "diff_file":   str(diff_path.relative_to(ROOT)).replace("\\", "/"),
        "added":       added,
        "removed":     removed,
    }
    map_path.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  mapping[{variant}] = +{added} -{removed} ({description})")
    print(f"  → {map_path.relative_to(ROOT)}")
    return 0


def cmd_list() -> int:
    PATTERNS.mkdir(parents=True, exist_ok=True)
    exps  = sorted(PATTERNS.glob("*.exp"))
    diffs = sorted(PATTERNS.glob("*.diff"))
    print(f"captures ({len(exps)}):")
    for p in exps:
        print(f"  - {p.name}  ({p.stat().st_size} bytes)")
    print(f"diffs ({len(diffs)}):")
    for p in diffs:
        print(f"  - {p.name}  ({p.stat().st_size} bytes)")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "capture":
        return cmd_capture(args[0]) if args else (print("usage: capture <label>") or 1)
    if cmd == "diff":
        return cmd_diff(args[0], args[1]) if len(args) >= 2 else (print("usage: diff <baseline> <variant>") or 1)
    if cmd == "mapping":
        return cmd_mapping(args[0], " ".join(args[1:])) if args else (print("usage: mapping <variant> [설명]") or 1)
    if cmd == "list":
        return cmd_list()
    print(f"[ERROR] unknown command: {cmd}")
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
