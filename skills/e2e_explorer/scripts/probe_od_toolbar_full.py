#!/usr/bin/env python3
"""OD toolbar 전체 — control_type 무관 + 모든 hover tooltip 매핑.

이전 probe(probe_od_toolbar_all8)는 Button만 찾아 6개만 잡힘.
User 정보(8개)에 따르면 Remove/Add Sub-Index가 누락. RibbonButton/Image 등 다른 type일 가능성.
"""
import sys, time, json
from pathlib import Path
from pywinauto import mouse

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab


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
    time.sleep(2.0)

    # toolbar 영역 (x=260~700, y=110~170)의 모든 컨트롤 (Button/Image/Custom/Pane)
    print("=== Toolbar 영역 (x=260~700, y=110~170) 모든 control ===")
    candidates = []
    for d in win.descendants():
        try:
            r = d.rectangle()
            if 260 < r.left < 700 and 105 < r.top < 165 and r.width() < 80 and r.height() < 60 and r.width() > 10:
                ct = d.element_info.control_type
                # 클릭 가능 후보만
                if ct in ("Button", "Image", "Custom", "MenuItem", "ToggleButton"):
                    candidates.append((d, r, ct))
        except Exception: pass
    # dedupe by rect
    seen = set(); uniq = []
    for d, r, ct in candidates:
        key = (r.left, r.top, r.right, r.bottom)
        if key not in seen: seen.add(key); uniq.append((d, r, ct))
    uniq.sort(key=lambda x: x[1].left)
    print(f"후보 {len(uniq)}개")
    for i, (d, r, ct) in enumerate(uniq):
        print(f"  [{i}] {ct:14s} rect=({r.left},{r.top},{r.right},{r.bottom})")

    # Each → hover tooltip
    print("\n=== Hover tooltip 각 후보 (1.5초 대기) ===")
    tooltips = {}
    for i, (d, r, ct) in enumerate(uniq):
        cx, cy = (r.left+r.right)//2, (r.top+r.bottom)//2
        mouse.move(coords=(1500, 800))
        time.sleep(0.5)
        mouse.move(coords=(cx, cy))
        time.sleep(1.5)
        tip = None
        for tt in win.descendants(control_type="ToolTip"):
            try:
                tn = tt.window_text()
                if tn and tn.strip():
                    tip = tn; break
            except Exception: pass
        tooltips[i] = tip
        print(f"  [{i}] {ct:14s} @({cx},{cy}) → {tip!r}")

    OUT = ROOT / "logs" / "probe_od_toolbar_full.json"
    OUT.write_text(json.dumps({
        "candidates": [{"idx": i, "type": ct, "rect": [r.left, r.top, r.right, r.bottom], "tooltip": tooltips.get(i)}
                       for i, (d, r, ct) in enumerate(uniq)]
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
