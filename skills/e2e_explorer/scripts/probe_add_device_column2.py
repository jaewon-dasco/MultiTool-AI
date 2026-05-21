#!/usr/bin/env python3
"""Probe: Add Device family 클릭 후 Device 컬럼(x=428-475) 실제 텍스트 dump.

흐름:
1. MultiTool 연결 (기존 실행 가정)
2. Add Device DropDownPart 클릭 → 4-column ListMenu 등장
3. Product family 컬럼에서 '3000 series' 클릭
4. 1.5s 대기 후 Device 컬럼의 Text/ListItem 트리 dump
5. logs/probe_add_device_column2.json
"""
import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "logs" / "probe_add_device_column2.json"


def dump_area(win, x_range, y_min=140, y_max=600):
    """x 범위 + y 범위 안의 모든 컨트롤 dump."""
    items = []
    xmin, xmax = x_range
    for t in ["Text", "ListItem", "Button", "DataItem", "Custom", "Group", "Pane"]:
        try:
            for c in win.descendants(control_type=t):
                try:
                    r = c.rectangle()
                    if (xmin - 5) <= r.left <= (xmax + 5) and y_min < r.top < y_max:
                        items.append({
                            "type": t,
                            "name": (c.window_text() or "")[:120],
                            "rect": [r.left, r.top, r.right, r.bottom],
                            "size": [r.width(), r.height()],
                        })
                except Exception: pass
        except Exception: pass
    return items


def main():
    from skills.e2e_explorer.recipes import common
    from skills.e2e_explorer.recipes.add_device_recipe import find_add_device_dropdowns, select_column_item, COLUMN_X

    app, win = common.connect()
    common.ensure_maximized(win)

    print("Step 0: switch to Network Editor tab")
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor":
                t.click_input(); time.sleep(1.0); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)

    print("Step 1: locate DropDownParts")
    drops = find_add_device_dropdowns(win)
    print(f"  {len(drops)} dropdowns")
    if not drops:
        print("FAIL: no dropdowns"); return 1

    print("Step 2: click Add Device DropDownPart [0]")
    drops[0][0].click_input()
    time.sleep(1.8)

    print("Step 3: dump column 1 (family) BEFORE clicking")
    fam_before = dump_area(win, COLUMN_X["family"])
    print(f"  family column: {len(fam_before)} controls")

    print("Step 4: dump column 2 (Device) BEFORE family click")
    dev_before = dump_area(win, COLUMN_X["device"])
    print(f"  device column (empty): {len(dev_before)} controls")

    print("Step 5: click family '3000 series'")
    ok = select_column_item(win, COLUMN_X["family"], "3000 series")
    print(f"  family click ok={ok}")
    if not ok:
        OUT.write_text(json.dumps({"err":"family click failed",
                                   "family_before": fam_before,
                                   "dev_before": dev_before},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
        from pywinauto.keyboard import send_keys; send_keys("{ESC}")
        return 1

    print("Step 6: wait 2s + dump Device column AFTER family click")
    time.sleep(2.0)
    dev_after = dump_area(win, COLUMN_X["device"])
    print(f"  device column populated: {len(dev_after)} controls")

    # Filter Text type for readability
    dev_texts = [c for c in dev_after if c["type"] == "Text" and c["name"]]
    print("\nDevice column TEXT entries (after family click):")
    for c in dev_texts[:20]:
        print(f"  rect={c['rect']} h={c['size'][1]:3} name={c['name']!r}")

    # Also wider x range to catch nearby controls
    print("\nWider x scan (x=420-490, after family click):")
    wider = dump_area(win, (420, 490))
    for c in wider[:30]:
        if c["type"] in ("Text", "ListItem", "Button") and c["name"]:
            print(f"  {c['type']:10} rect={c['rect']} name={c['name'][:60]!r}")

    OUT.write_text(json.dumps({
        "family_before": fam_before,
        "dev_before": dev_before,
        "dev_after": dev_after,
        "wider_after": wider,
        "column_x_device": COLUMN_X["device"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")

    # close menu
    from pywinauto.keyboard import send_keys; send_keys("{ESC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
