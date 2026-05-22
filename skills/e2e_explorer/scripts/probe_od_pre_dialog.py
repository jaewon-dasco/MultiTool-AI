#!/usr/bin/env python3
"""'Pre-Defined Index' 다이얼로그 내부 구조 probe.

흐름:
1. Configure + OD tab → idx=0 클릭 → 'Pre-Defined Index' 다이얼로그 등장
2. win32 backend로 다이얼로그 connect
3. 모든 컨트롤 dump (특히 Variable/Array/Record 키워드)
"""
import sys, time, json
from pathlib import Path
from pywinauto import Desktop, Application

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "logs" / "probe_od_pre_dialog.json"


def walk_dialog(dlg, depth=0, out=None, limit=300):
    if out is None: out = []
    if len(out) >= limit: return out
    try:
        r = dlg.rectangle()
        out.append({
            "d": depth,
            "class": dlg.class_name(),
            "name": (dlg.window_text() or "")[:120],
            "rect": [r.left, r.top, r.right, r.bottom],
        })
    except Exception:
        return out
    if depth > 12: return out
    try:
        for ch in dlg.children(): walk_dialog(ch, depth+1, out, limit)
    except Exception: pass
    return out


def main():
    from skills.e2e_explorer.recipes import common
    from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab
    from skills.e2e_explorer.recipes.od_recipe import find_od_toolbar_buttons

    app, win = common.connect()
    common.ensure_maximized(win)

    print("Step 0: Network Editor + Configure + OD tab")
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)
    if not open_configure_panel(win, "CU_3606_21_1"):
        print("FAIL: configure"); return 1
    time.sleep(1)
    if not click_left_tab(win, "Object Dictionary"):
        print("FAIL: OD tab"); return 1
    time.sleep(2)

    print("Step 1: click idx=0 (Pre-Defined Index)")
    btns = find_od_toolbar_buttons(win)
    if not btns:
        print("FAIL: no buttons"); return 1
    btns[0][0].click_input()
    time.sleep(2.5)

    print("Step 2: locate 'Pre-Defined Index' dialog (win32)")
    target_dlg = None
    for w in Desktop(backend="win32").windows():
        try:
            t = w.window_text() or ""
            if "Pre-Defined" in t or "Predefined" in t:
                target_dlg = w
                print(f"  found hwnd={w.handle} title={t!r}")
                break
        except Exception: pass

    if not target_dlg:
        # try UIA
        print("  not in win32, try UIA descendants under main window")
        from skills.e2e_explorer.recipes import common
        app2, win2 = common.connect()
        for c in win2.descendants(control_type="Window"):
            try:
                t = c.window_text() or ""
                if "Pre-Defined" in t:
                    target_dlg = c
                    print(f"  found UIA Window: {t!r}")
                    break
            except Exception: pass

    if not target_dlg:
        print("FAIL: dialog not found"); return 1

    print("Step 3: dump dialog tree (win32)")
    try:
        # Try connect via Application for richer access
        a = Application(backend="win32").connect(handle=target_dlg.handle)
        dlg_top = a.top_window()
        tree = walk_dialog(dlg_top)
    except Exception as e:
        print(f"  Application connect FAIL: {e}, fallback to direct")
        tree = walk_dialog(target_dlg)

    print(f"  {len(tree)} controls")
    for item in tree[:60]:
        n = item.get("name", "")
        cls = item.get("class", "")
        if n or cls in ("ComboBox", "Edit", "ListBox", "TreeView", "ListView"):
            print(f"  d={item['d']:2} class={cls:20} name={n[:60]!r} rect={item['rect']}")

    # Also try UIA-style scan inside dialog
    print("\nStep 4: UIA scan within dialog rect for Variable/Array/Record keywords")
    app2, win2 = common.connect()
    dr = target_dlg.rectangle()
    print(f"  dialog rect={dr.left},{dr.top},{dr.right},{dr.bottom}")
    keywords = ["Variable", "Array", "Record", "Type", "Index"]
    for c in win2.descendants():
        try:
            r = c.rectangle()
            if dr.left <= r.left and r.right <= dr.right and dr.top <= r.top and r.bottom <= dr.bottom:
                n = (c.window_text() or "").strip()
                if any(k in n for k in keywords):
                    print(f"  {c.element_info.control_type:12} rect={[r.left,r.top,r.right,r.bottom]} name={n[:60]!r}")
        except Exception: pass

    OUT.write_text(json.dumps({"tree": tree}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")

    from pywinauto.keyboard import send_keys; send_keys("{ESC}"); time.sleep(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
