#!/usr/bin/env python3
"""OD Add Index dialog probe — Variable/Array/Record 타입 선택 확인.

흐름:
1. Configure panel + OD tab 진입
2. Baseline tree dump
3. OD toolbar idx=0 (Add Index) 클릭
4. 다이얼로그/패널 등장 대기 + after dump
5. NEW controls 식별 + win32 dialog 탐색
"""
import sys, time, json
from pathlib import Path
from pywinauto import Desktop

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "logs" / "probe_od_add_index.json"


def walk(c, d=0, out=None, limit=1000):
    if out is None: out = []
    if len(out) >= limit: return out
    try:
        r = c.rectangle()
        out.append({"d": d, "type": c.element_info.control_type,
                    "name": (c.window_text() or "")[:120],
                    "rect": [r.left, r.top, r.right, r.bottom]})
    except Exception: return out
    if d > 15: return out
    try:
        for ch in c.children(): walk(ch, d+1, out, limit)
    except Exception: pass
    return out


def main():
    from skills.e2e_explorer.recipes import common
    from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab
    from skills.e2e_explorer.recipes.od_recipe import click_od_toolbar_idx

    app, win = common.connect()
    common.ensure_maximized(win)

    print("Step 0: ensure Network Editor tab")
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)

    print("Step 1: Configure + OD tab")
    if not open_configure_panel(win, "CU_3606_21_1"):
        print("FAIL: configure panel"); return 1
    time.sleep(1.0)
    if not click_left_tab(win, "Object Dictionary"):
        print("FAIL: OD tab"); return 1
    time.sleep(2.0)

    print("Step 2: baseline tree + win32 windows")
    before = walk(win)
    print(f"  baseline {len(before)} controls")
    before_keys = {(c["type"], tuple(c["rect"])) for c in before}

    win32_before = []
    for w in Desktop(backend="win32").windows():
        try:
            t = w.window_text()
            if t and "MultiTool Creator" not in t and len(t) < 100:
                win32_before.append((w.handle, t))
        except Exception: pass
    print(f"  win32 win count: {len(win32_before)}")

    print("Step 3: click OD toolbar idx=0 (Add Index)")
    r = click_od_toolbar_idx(win, idx=0, after_row_select=False)
    print(f"  clicked: {r}")
    if not r.get("ok"):
        return 1
    time.sleep(2.5)

    print("Step 4: after dump")
    after = walk(win)
    new_ctrls = [c for c in after if (c["type"], tuple(c["rect"])) not in before_keys]
    print(f"  after {len(after)} controls, NEW {len(new_ctrls)}")

    print("\nNEW UIA controls (sorted by y):")
    new_ctrls.sort(key=lambda x: (x["rect"][1], x["rect"][0]))
    for c in new_ctrls:
        if c["type"] in ("Window","Dialog","Pane","Group","List","ListItem","TreeItem",
                          "ComboBox","Text","Button","DataItem","Custom","Edit","CheckBox","RadioButton"):
            name = c["name"]
            print(f"  d={c['d']:2} {c['type']:12} rect={c['rect']} name={name[:80]!r}")

    # win32 dialog
    print("\nwin32 NEW windows:")
    win32_after = []
    for w in Desktop(backend="win32").windows():
        try:
            t = w.window_text()
            if t and "MultiTool Creator" not in t and len(t) < 100:
                win32_after.append((w.handle, t, w.rectangle()))
        except Exception: pass
    before_hwnds = {h for h, _ in win32_before}
    for hwnd, title, rect in win32_after:
        if hwnd not in before_hwnds:
            print(f"  hwnd={hwnd} title={title!r} rect={rect}")

    OUT.write_text(json.dumps({
        "before_n": len(before), "after_n": len(after),
        "new_controls": new_ctrls,
        "win32_new": [{"hwnd": h, "title": t, "rect": list(r)[:4] if hasattr(r,'__iter__') else None}
                      for h,t,r in win32_after if h not in before_hwnds],
    }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nDump: {OUT}")

    from pywinauto.keyboard import send_keys; send_keys("{ESC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
