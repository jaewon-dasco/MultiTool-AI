#!/usr/bin/env python3
"""OD 행 선택 후 toolbar 변화 — Remove/Add Sub-Index 등장 여부."""
import sys, time, json
from pathlib import Path
from pywinauto import mouse

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab


def find_toolbar_buttons(win, x_min=260, x_max=700, y_min=105, y_max=165):
    btns = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            if x_min < r.left < x_max and y_min < r.top < y_max and 10 < r.width() < 80:
                btns.append((b, r))
        except Exception: pass
    btns.sort(key=lambda x: x[1].left)
    return btns


def hover_get_tip(win, btn):
    r = btn.rectangle()
    cx, cy = (r.left+r.right)//2, (r.top+r.bottom)//2
    mouse.move(coords=(1700, 800)); time.sleep(0.4)
    mouse.move(coords=(cx, cy)); time.sleep(1.0)
    for tt in win.descendants(control_type="ToolTip"):
        try:
            tn = tt.window_text()
            if tn and tn.strip(): return tn
        except Exception: pass
    return None


def main():
    app, win = common.connect()
    common.ensure_maximized(win)
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)
    if not open_configure_panel(win, "CU_3606_21_1"): return 1
    time.sleep(1.5)
    if not click_left_tab(win, "Object Dictionary"): return 1
    time.sleep(2.5)

    # 1. 행 선택 전 toolbar
    print("=== Before row select ===")
    btns0 = find_toolbar_buttons(win)
    print(f"buttons: {len(btns0)}")
    for i, (b, r) in enumerate(btns0):
        print(f"  [{i}] rect=({r.left},{r.top},{r.right},{r.bottom})")

    # 2. 첫 OD 데이터 행 클릭 (DataItem)
    print("\n=== Click first OD row (DataItem) ===")
    target = None
    for d in win.descendants(control_type="DataItem"):
        try:
            r = d.rectangle()
            # OD 데이터 영역: y > 180
            if r.top > 180 and r.height() > 5 and r.width() > 100:
                target = d; break
        except Exception: pass
    if target is None:
        print("FAIL: no DataItem"); return 1
    tr = target.rectangle()
    print(f"  DataItem rect={tr}")
    target.click_input()
    time.sleep(1.5)

    # 3. 행 선택 후 toolbar 다시 검색
    print("\n=== After row select ===")
    btns1 = find_toolbar_buttons(win)
    print(f"buttons: {len(btns1)}")
    for i, (b, r) in enumerate(btns1):
        tip = hover_get_tip(win, b)
        print(f"  [{i}] rect=({r.left},{r.top},{r.right},{r.bottom}) tooltip={tip!r}")

    OUT = ROOT / "logs" / "probe_od_after_rowselect.json"
    OUT.write_text(json.dumps({
        "before": [{"rect": [r.left, r.top, r.right, r.bottom]} for b, r in btns0],
        "after": [{"rect": [r.left, r.top, r.right, r.bottom]} for b, r in btns1],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
