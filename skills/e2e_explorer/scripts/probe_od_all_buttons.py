#!/usr/bin/env python3
"""OD 탭 진입 후 모든 Button 컨트롤을 전수조사.

목적: idx=0 클릭이 dialog 안 여는 원인 진단.
- 모든 Button의 rect, name, automation_id, ToolTip 식별
- enabled 상태 확인
- OD toolbar 영역(y=105~165) 외에도 Add Index가 있을 수 있음 — 전체 스캔
"""
import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "logs" / "probe_od_all_buttons.json"


def main():
    from skills.e2e_explorer.recipes import common
    from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab

    app, win = common.connect()
    common.ensure_maximized(win)

    print("Step 0: Network Editor tab")
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)

    print("Step 1: Configure + OD tab")
    if not open_configure_panel(win, "CU_3606_21_1"):
        print("FAIL: configure"); return 1
    time.sleep(1)
    if not click_left_tab(win, "Object Dictionary"):
        print("FAIL: OD tab"); return 1
    time.sleep(2)

    print("Step 2: dump ALL Button controls")
    buttons = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            name = b.window_text() or ""
            auto_id = ""
            try: auto_id = b.automation_id() or ""
            except Exception: pass
            enabled = True
            try: enabled = b.is_enabled()
            except Exception: pass
            buttons.append({
                "name": name[:80],
                "auto_id": auto_id[:80],
                "rect": [r.left, r.top, r.right, r.bottom],
                "size": [r.width(), r.height()],
                "enabled": enabled,
            })
        except Exception: pass

    print(f"  total {len(buttons)} Buttons")

    # Sort by y then x
    buttons.sort(key=lambda b: (b["rect"][1], b["rect"][0]))

    print("\nButtons in OD toolbar area (y < 250, x > 200, narrow widths):")
    for b in buttons:
        r = b["rect"]
        if r[1] < 250 and r[0] > 200 and 10 < b["size"][0] < 100:
            print(f"  rect={r} h={b['size'][1]:3} en={b['enabled']!s:5} "
                  f"name={b['name']!r} id={b['auto_id']!r}")

    print(f"\nButtons with non-empty name (any location):")
    for b in buttons:
        if b["name"].strip() and len(b["name"]) < 40:
            r = b["rect"]
            print(f"  rect={r} en={b['enabled']!s:5} name={b['name']!r}")

    OUT.write_text(json.dumps({"buttons": buttons}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
