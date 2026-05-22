#!/usr/bin/env python3
"""OD toolbar fix (4ec93ab) 검증 + 'Use Selected/Original' 다이얼로그 감지/dismiss.

흐름:
1. Network Editor + Configure + OD tab
2. fix 적용 후 find_od_toolbar_buttons() 결과 7개 버튼 출력 (idx/enabled)
3. 'Use Selected/Original' 다이얼로그 존재 시 cancel 클릭 → dismiss
4. dismiss 후 다시 버튼 enabled 상태 재확인
5. idx=0 (예상: Add Index, en=True) 클릭 → win32 다이얼로그 등장 확인
"""
import sys, time, json
from pathlib import Path
from pywinauto import Desktop

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "logs" / "probe_od_verify_fix.json"


def dump_buttons(buttons_with_rect, label):
    print(f"\n{label}: {len(buttons_with_rect)} buttons")
    for i, (b, r) in enumerate(buttons_with_rect):
        try:
            en = b.is_enabled()
        except Exception:
            en = "?"
        name = b.window_text() or ""
        print(f"  idx={i} rect=[{r.left},{r.top},{r.right},{r.bottom}] en={en!s:5} name={name!r}")


def list_win32_modal_windows():
    out = []
    for w in Desktop(backend="win32").windows():
        try:
            t = w.window_text() or ""
            if t and "MultiTool Creator" not in t and 0 < len(t) < 100:
                r = w.rectangle()
                out.append({"hwnd": w.handle, "title": t,
                            "rect": [r.left, r.top, r.right, r.bottom]})
        except Exception: pass
    return out


def find_use_selected_dialog(win):
    """'Use Selected (Use Original)' Confirm/Recovery 다이얼로그 탐색.
    Returns OK_button rect or None."""
    # UIA Button name search
    for b in win.descendants(control_type="Button"):
        try:
            n = (b.window_text() or "").strip()
            if "Use Selected" in n or "Use Original" in n:
                # Found one - find the OK (Use Selected)
                if "Selected" in n:
                    return b
        except Exception: pass
    return None


def main():
    from skills.e2e_explorer.recipes import common
    from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab
    from skills.e2e_explorer.recipes.od_recipe import find_od_toolbar_buttons

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

    print("Step 2: find_od_toolbar_buttons() - 4ec93ab fix 적용 결과")
    btns = find_od_toolbar_buttons(win)
    dump_buttons(btns, "OD toolbar buttons")

    print("\nStep 3: 'Use Selected' 다이얼로그 탐색")
    use_btn = find_use_selected_dialog(win)
    if use_btn:
        rect = use_btn.rectangle()
        print(f"  FOUND 'Use Selected' button @ {rect}")
        # 'Cancel (Use Original)' 클릭이 안전 - 변경 없이 dismiss
        cancel_btn = None
        for b in win.descendants(control_type="Button"):
            try:
                n = (b.window_text() or "").strip()
                if "Use Original" in n or "Cancel" in n:
                    cancel_btn = b; break
            except Exception: pass
        if cancel_btn:
            print(f"  clicking 'Cancel (Use Original)' to dismiss")
            cancel_btn.click_input()
            time.sleep(2)
        else:
            print(f"  no Cancel button found, sending ESC")
            from pywinauto.keyboard import send_keys; send_keys("{ESC}")
            time.sleep(2)
    else:
        print("  no 'Use Selected' dialog detected")

    print("\nStep 4: dismiss 후 버튼 재확인")
    btns2 = find_od_toolbar_buttons(win)
    dump_buttons(btns2, "OD toolbar buttons (after dismiss)")

    print("\nStep 5: idx=0 클릭 (Add Index 예상) + win32 다이얼로그 등장 확인")
    if btns2:
        win32_before = {w["hwnd"] for w in list_win32_modal_windows()}
        btns2[0][0].click_input()
        time.sleep(2.5)
        win32_after = list_win32_modal_windows()
        new_dlgs = [w for w in win32_after if w["hwnd"] not in win32_before]
        print(f"  new win32 dialogs: {len(new_dlgs)}")
        for d in new_dlgs:
            print(f"    hwnd={d['hwnd']} title={d['title']!r} rect={d['rect']}")

    OUT.write_text(json.dumps({
        "fix_applied": "TOOLBAR_X_MIN 260→220",
        "buttons_initial": [{"rect":[r.left,r.top,r.right,r.bottom],
                             "enabled": (b.is_enabled() if hasattr(b,'is_enabled') else None)}
                             for b,r in btns],
        "use_selected_dialog_found": use_btn is not None,
    }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
