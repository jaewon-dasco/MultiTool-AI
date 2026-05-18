#!/usr/bin/env python3
"""Probe I/O 패널 OCR 가시성.

흐름:
  1. MultiTool 연결 (이미 띄워져 있어야 함, 프로젝트 로드 상태)
  2. CU_3606_21_1 → Configure → I/O 탭 진입
  3. 전체 화면 OCR → 모든 텍스트 dump
  4. 기대 라벨(VAVLE_UP, VAVLE_DN, LED1, LED2, X1_9~12, Modes, Variable Name)이 OCR에 잡히는지 보고
  5. logs/probe_io_panel.json에 저장

판정:
  - 라벨 다수 발견 → set_field_auto + table_column fix만으로 해결될 가능성 큼
  - 라벨 미발견 → I/O 탭 진입 실패 또는 OCR이 Edit 셀 내부 못 읽음 (별도 해결 필요)
"""
import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes import common, ocr_helpers
from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab

DEVICE = "CU_3606_21_1"
TAB = "I/O"
EXPECTED_LABELS = [
    "VAVLE_UP", "VAVLE_DN", "LED1", "LED2",
    "X1_9", "X1_10", "X1_11", "X1_12",
    "Modes", "Variable Name", "Active", "Filter",
]
OUT = ROOT / "logs" / "probe_io_panel.json"


def main():
    app, win = common.connect()
    common.ensure_maximized(win)

    if not open_configure_panel(win, DEVICE):
        print("FAIL: open Configure panel"); return 1
    time.sleep(1.5)

    if not click_left_tab(win, TAB):
        print(f"FAIL: tab '{TAB}'"); return 1
    time.sleep(2.0)

    print("OCR 시작...")
    ocr = ocr_helpers.ocr_screen()
    print(f"전체 OCR 결과: {len(ocr)} 텍스트 아이템")

    # 기대 라벨별 hit 여부
    findings = {}
    for label in EXPECTED_LABELS:
        hits = []
        for it in ocr:
            t = it.get("text", "").lower()
            if label.lower() in t:
                hits.append({"text": it["text"], "x": it["x"], "y": it["y"], "right": it["right"], "yc": it["yc"]})
        findings[label] = {"count": len(hits), "hits": hits[:5]}

    # Variable name 컬럼 후보
    sample = [{"text": it["text"], "x": it["x"], "y": it["y"]} for it in ocr[:50]]

    out = {
        "tab": TAB,
        "device": DEVICE,
        "total_ocr_items": len(ocr),
        "findings": findings,
        "first_50_ocr_items": sample,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== Findings ===")
    for label, info in findings.items():
        status = "✓" if info["count"] > 0 else "✗"
        print(f"  {status} {label:15s} count={info['count']}")
    print(f"\nFull dump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
