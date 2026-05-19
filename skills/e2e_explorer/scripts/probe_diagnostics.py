#!/usr/bin/env python3
"""Diagnostics 탭 click_table_cell 실패 원인 분석.

가설:
  - 야간 사이클 0/24 모두 ui_change_failed
  - click_table_cell(row='Temperature', col='Minimum') → find_label("Temperature") 실패?
  - 또는 셀 클릭 후 Edit 진입 안 되는 문제?
"""
import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common, ocr_helpers
from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab

OUT = ROOT / "logs" / "probe_diagnostics.json"


def main():
    app, win = common.connect()
    common.ensure_maximized(win)
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)
    if not open_configure_panel(win, "CU_3606_21_1"):
        print("FAIL configure"); return 1
    time.sleep(1.5)
    if not click_left_tab(win, "Diagnostics"):
        print("FAIL Diagnostics tab"); return 1
    time.sleep(2.5)

    # OCR
    print("=== OCR scan ===")
    ocr = ocr_helpers.ocr_screen()
    print(f"OCR items: {len(ocr)}")

    # find_label 가시성 검증
    targets_row = ["Temperature", "SupplyVoltage", "Ref5V", "CycleTime"]
    targets_col = ["Minimum", "Maximum", "Default"]
    out = {"ocr_count": len(ocr), "row_hits": {}, "col_hits": {}}

    for t in targets_row + targets_col:
        hits = [it for it in ocr if t.lower() in it["text"].lower()]
        out["row_hits" if t in targets_row else "col_hits"][t] = [
            {"text": h["text"], "x": h["x"], "y": h["y"], "yc": h["yc"], "xc": h["xc"]}
            for h in hits[:3]
        ]
    print("Row labels (Temperature etc):")
    for k, v in out["row_hits"].items():
        print(f"  {k!r}: {len(v)} hits — {[h['text'] for h in v]}")
    print("Col labels (Minimum/Maximum/Default):")
    for k, v in out["col_hits"].items():
        print(f"  {k!r}: {len(v)} hits — {[h['text'] for h in v]}")

    # try click_table_cell
    print("\n=== click_table_cell('Temperature', 'Minimum') ===")
    coords = ocr_helpers.click_table_cell("Temperature", "Minimum")
    print(f"  coords={coords}")
    if coords:
        # 클릭 후 화면 변화
        time.sleep(0.5)
        ocr2 = ocr_helpers.ocr_screen()
        diff = len(ocr2) - len(ocr)
        print(f"  OCR diff after click: {diff:+d}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
