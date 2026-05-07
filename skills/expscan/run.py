"""expscan/run.py — .exp 생성 패턴 분석 v1

서브명령:
  capture <label>                  현재 .exp 를 label.exp 로 저장
  diff    <baseline> <variant>     두 캡처 비교 → variant.diff 생성
  mapping <variant> [설명]         mapping.json 갱신
  list                             캡처·diff 목록
  plan                             수집할 variant 후보 출력 (TODO 리스트)
  validate                         mapping.json 스키마/누락 검증

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


# 권장 variant 카탈로그 — 단일 설정 변경별 관찰 가치가 높은 항목
PLAN_CATALOG: list[dict] = [
    {"label": "bitrate_500",    "change": "CAN1 Bit Rate 250→500",     "category": "network"},
    {"label": "bitrate_125",    "change": "CAN1 Bit Rate 250→125",     "category": "network"},
    {"label": "buffering_off",  "change": "CAN1 Buffering Enabled→해제", "category": "network"},
    {"label": "od_add_2300",    "change": "OD 0x2300 신규 인덱스 추가",  "category": "od"},
    {"label": "od_remove_2300", "change": "OD 0x2300 삭제",              "category": "od"},
    {"label": "rpdo_add",       "change": "RPDO 매핑 1줄 추가",          "category": "pdo"},
    {"label": "tpdo_add",       "change": "TPDO 매핑 1줄 추가",          "category": "pdo"},
    {"label": "device_clone",   "change": "Device 1대 Clone Unit",       "category": "device"},
    {"label": "j1939_enable",   "change": "J1939 활성화",                "category": "protocol"},
    {"label": "isobus_enable",  "change": "ISOBUS 활성화",               "category": "protocol"},
]


def cmd_plan() -> int:
    """수집 대상 variant 카탈로그 출력. 이미 캡처된 항목은 [done] 표시."""
    PATTERNS.mkdir(parents=True, exist_ok=True)
    map_path = PATTERNS / "mapping.json"
    mapping  = {}
    if map_path.exists():
        mapping = json.loads(map_path.read_text(encoding="utf-8"))

    print("variant 캡처 카탈로그:")
    print(f"{'#':>3}  {'label':18s}  {'category':10s}  status   change")
    print("-" * 80)
    for i, item in enumerate(PLAN_CATALOG, 1):
        label  = item["label"]
        exp_ok = (PATTERNS / f"{label}.exp").exists()
        map_ok = label in mapping
        status = "done"  if exp_ok and map_ok else \
                 "exp"   if exp_ok            else \
                 "todo"
        print(f"{i:>3}  {label:18s}  {item['category']:10s}  {status:7s}  {item['change']}")
    print()
    print("절차: MultiTool에서 baseline 상태 확보 → 단일 설정 변경 → System Export →")
    print("  py skills/expscan/run.py capture <label>")
    print("  py skills/expscan/run.py diff baseline <label>")
    print("  py skills/expscan/run.py mapping <label> \"<change 설명>\"")
    return 0


def cmd_validate() -> int:
    """mapping.json 스키마·존재성 검증."""
    map_path = PATTERNS / "mapping.json"
    if not map_path.exists():
        print(f"[INFO] {map_path} 없음 — 캡처 0건")
        return 0
    mapping = json.loads(map_path.read_text(encoding="utf-8"))

    required_keys = {"description", "exp_file", "diff_file", "added", "removed"}
    errors: list[str] = []
    warns:  list[str] = []

    for label, entry in mapping.items():
        missing = required_keys - set(entry.keys())
        if missing:
            errors.append(f"  [{label}] 필수 키 누락: {missing}")
            continue
        exp_p  = ROOT / entry["exp_file"]
        diff_p = ROOT / entry["diff_file"]
        if not exp_p.exists():
            errors.append(f"  [{label}] exp_file 부재: {entry['exp_file']}")
        if not diff_p.exists():
            errors.append(f"  [{label}] diff_file 부재: {entry['diff_file']}")
        if entry["added"] == 0 and entry["removed"] == 0:
            warns.append(f"  [{label}] diff 변화 0 — 캡처 의미 없음")

    catalog_labels = {it["label"] for it in PLAN_CATALOG}
    uncovered      = catalog_labels - set(mapping.keys())

    print(f"mapping entries: {len(mapping)}")
    print(f"errors: {len(errors)}")
    for e in errors: print(e)
    print(f"warnings: {len(warns)}")
    for w in warns:  print(w)
    print(f"카탈로그 미수집 ({len(uncovered)}/{len(catalog_labels)}):")
    for u in sorted(uncovered): print(f"  - {u}")
    return 0 if not errors else 1


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
    if cmd == "plan":
        return cmd_plan()
    if cmd == "validate":
        return cmd_validate()
    print(f"[ERROR] unknown command: {cmd}")
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
