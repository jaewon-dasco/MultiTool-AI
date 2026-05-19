#!/usr/bin/env python3
"""OD 탭의 모든 Button + 인접 Text/Image — 이름 없는 toolbar 버튼 식별."""
import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import click_left_tab, open_configure_panel

OUT = ROOT / "logs" / "probe_od_toolbar.json"


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
    time.sleep(1.2)
    if not click_left_tab(win, "Object Dictionary"):
        print("FAIL OD tab"); return 1
    time.sleep(2)

    # 우측 메인 영역의 모든 Button (x>250, 이름 무관)
    print("=== Main area toolbar Buttons (x>250) ===")
    btns = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            if r.left > 250 and r.top < 250 and r.width() < 80 and r.height() < 50:
                btns.append((b, r))
        except Exception: pass
    btns.sort(key=lambda x: (x[1].top, x[1].left))
    for i, (b, r) in enumerate(btns[:30]):
        name = b.window_text() or ''
        # 인접 Text/Tooltip 찾기
        tip = None
        try:
            # 아래쪽 Text
            for t in win.descendants(control_type="Text"):
                try:
                    tr = t.rectangle()
                    if abs(tr.left - r.left) < 30 and r.bottom <= tr.top <= r.bottom + 50:
                        tip = t.window_text(); break
                except Exception: pass
        except Exception: pass
        print(f"  [{i:2d}] rect=({r.left},{r.top},{r.right},{r.bottom}) name={name!r} adj_text={tip!r}")

    # 또한 모든 Text를 dump (텍스트 라벨도 클릭 가능한 toolbar item일 수 있음)
    print("\n=== Top-region Text labels (y<200, x>250) ===")
    for t in win.descendants(control_type="Text"):
        try:
            r = t.rectangle()
            txt = t.window_text() or ""
            if r.left > 250 and r.top < 200 and 5 < r.height() < 40 and txt and len(txt) < 50:
                print(f"  '{txt}' rect=({r.left},{r.top},{r.right},{r.bottom})")
        except Exception: pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
