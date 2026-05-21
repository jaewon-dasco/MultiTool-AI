#!/usr/bin/env python3
"""Probe: Device 선택 후 CODESYS Version 컬럼 텍스트 dump."""
import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "logs" / "probe_add_device_cds.json"


def dump_area(win, x_range, y_min=140, y_max=600):
    items = []
    xmin, xmax = x_range
    for t in ["Text", "ListItem", "Button"]:
        try:
            for c in win.descendants(control_type=t):
                try:
                    r = c.rectangle()
                    if (xmin - 5) <= r.left <= (xmax + 5) and y_min < r.top < y_max:
                        items.append({"type": t, "name": (c.window_text() or "")[:120],
                                      "rect": [r.left, r.top, r.right, r.bottom]})
                except Exception: pass
        except Exception: pass
    return items


def main():
    from skills.e2e_explorer.recipes import common
    from skills.e2e_explorer.recipes.add_device_recipe import (
        find_add_device_dropdowns, select_column_item, _select_column_item_contains,
        select_first_in_column, COLUMN_X)

    app, win = common.connect()
    common.ensure_maximized(win)

    # Switch to Network Editor
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)

    print("Step 1: open Add Device dropdown")
    drops = find_add_device_dropdowns(win)
    drops[0][0].click_input(); time.sleep(1.8)

    print("Step 2: family '3000 series'")
    assert select_column_item(win, COLUMN_X["family"], "3000 series")
    time.sleep(1.5)

    print("Step 3: device 'CU_3606_21' (양방향 contains)")
    ok = _select_column_item_contains(win, COLUMN_X["device"], "CU_3606_21", timeout=4.0)
    print(f"  device match ok={ok}")
    if not ok:
        from pywinauto.keyboard import send_keys; send_keys("{ESC}")
        return 1
    time.sleep(1.5)

    print("Step 4: dump CDS column (wide x=580-720)")
    cds_area = dump_area(win, (580, 720))
    print(f"  {len(cds_area)} controls")
    for c in cds_area:
        if c["name"]:
            print(f"  {c['type']:10} rect={c['rect']} name={c['name'][:80]!r}")

    print("\nStep 5: also dump entire row band (y=140-450, x=200-800)")
    wide = dump_area(win, (200, 800), y_min=140, y_max=450)
    text_only = [c for c in wide if c["type"]=="Text" and c["name"]]
    print(f"  Text entries: {len(text_only)}")
    for c in text_only[:30]:
        print(f"  rect={c['rect']} name={c['name'][:60]!r}")

    OUT.write_text(json.dumps({"cds_area": cds_area, "wide_text": text_only},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")

    from pywinauto.keyboard import send_keys; send_keys("{ESC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
