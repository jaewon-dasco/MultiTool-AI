#!/usr/bin/env python3
"""OD toolbar v2 — specific control_type 검색 (성능 개선)."""
import sys, time, json
from pathlib import Path
from pywinauto import mouse

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab


def main():
    print("[1] connect")
    app, win = common.connect()
    common.ensure_maximized(win)
    print("[2] Network Editor tab")
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)
    print("[3] open_configure_panel")
    if not open_configure_panel(win, "CU_3606_21_1"):
        print("FAIL configure"); return 1
    time.sleep(1.5)
    print("[4] click_left_tab OD")
    if not click_left_tab(win, "Object Dictionary"):
        print("FAIL OD tab"); return 1
    time.sleep(2.5)

    # 각 control_type 별 검색
    all_ctrls = []
    for ct in ("Button", "Image", "Custom", "MenuItem", "ToggleButton", "RadioButton", "Hyperlink", "SplitButton"):
        print(f"[5] search {ct}...")
        try:
            for d in win.descendants(control_type=ct):
                try:
                    r = d.rectangle()
                    if 260 < r.left < 700 and 105 < r.top < 165 and 10 < r.width() < 80 and r.height() < 60:
                        all_ctrls.append({"type": ct, "rect": [r.left, r.top, r.right, r.bottom],
                                          "name": (d.window_text() or "")[:60], "_obj": d})
                except Exception: pass
        except Exception: pass

    # dedupe by rect
    seen = set(); uniq = []
    for c in all_ctrls:
        key = tuple(c["rect"])
        if key not in seen: seen.add(key); uniq.append(c)
    uniq.sort(key=lambda c: c["rect"][0])

    print(f"\n=== Toolbar 후보 {len(uniq)}개 ===")
    for i, c in enumerate(uniq):
        print(f"  [{i}] {c['type']:14s} rect={c['rect']} name={c['name']!r}")

    # Each hover
    print("\n=== Hover tooltip ===")
    tooltips = {}
    for i, c in enumerate(uniq):
        r = c["rect"]
        cx, cy = (r[0]+r[2])//2, (r[1]+r[3])//2
        mouse.move(coords=(1700, 800)); time.sleep(0.5)
        mouse.move(coords=(cx, cy)); time.sleep(1.2)
        tip = None
        for tt in win.descendants(control_type="ToolTip"):
            try:
                tn = tt.window_text()
                if tn and tn.strip(): tip = tn; break
            except Exception: pass
        tooltips[i] = tip
        print(f"  [{i}] {c['type']:14s} @({cx},{cy}) → {tip!r}")

    OUT = ROOT / "logs" / "probe_od_toolbar_v2.json"
    OUT.write_text(json.dumps({
        "candidates": [{"idx": i, "type": c["type"], "rect": c["rect"], "name": c["name"], "tooltip": tooltips.get(i)}
                       for i, c in enumerate(uniq)]
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
