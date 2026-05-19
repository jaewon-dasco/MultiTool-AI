#!/usr/bin/env python3
"""OD toolbar Button[1] 클릭 → 다이얼로그 확인 (Pre-defined 가설)."""
import sys, time, json
from pathlib import Path
from pywinauto import Desktop
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import click_left_tab, open_configure_panel

OUT = ROOT / "logs" / "probe_od_btn1_dialog.json"


def walk(ctrl, depth=0, out=None, limit=400):
    if out is None: out = []
    if len(out) >= limit: return out
    try:
        r = ctrl.rectangle()
        out.append({"d": depth, "type": ctrl.element_info.control_type,
                    "name": (ctrl.window_text() or "")[:80],
                    "rect": [r.left, r.top, r.right, r.bottom]})
    except Exception: return out
    if depth > 15: return out
    try:
        for ch in ctrl.children(): walk(ch, depth+1, out, limit)
    except Exception: pass
    return out


def main():
    btn_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    app, win = common.connect()
    common.ensure_maximized(win)
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)
    if not open_configure_panel(win, "CU_3606_21_1"): return 1
    time.sleep(1.2)
    if not click_left_tab(win, "Object Dictionary"): return 1
    time.sleep(2)

    targets = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            if 260 < r.left < 600 and 110 < r.top < 170 and r.width() < 80:
                targets.append(b)
        except Exception: pass
    targets.sort(key=lambda b: b.rectangle().left)
    print(f"OD toolbar buttons: {len(targets)}")

    if btn_idx >= len(targets):
        print(f"FAIL: btn_idx {btn_idx} out of range"); return 1
    btn = targets[btn_idx]
    r = btn.rectangle()
    print(f"Click button [{btn_idx}] @ rect=({r.left},{r.top},{r.right},{r.bottom})")
    btn.click_input()
    time.sleep(2.0)

    # 새 다이얼로그 찾기
    titles = []
    new_dlg = None
    for w in app.windows():
        try:
            t = w.window_text()
            if t and "MultiTool" not in t:
                titles.append(t)
                if new_dlg is None and len(t) < 80: new_dlg = w
        except Exception: pass
    # win32 backend로 modal 다이얼로그도 확인
    for w in Desktop(backend="win32").windows():
        try:
            t = w.window_text() or ""
            if t and "MultiTool" not in t and len(t) < 80:
                titles.append(f"[win32] {t}")
        except Exception: pass
    print(f"Visible dialogs/titles: {titles}")

    if new_dlg:
        tree = walk(new_dlg)
        print(f"\nDialog tree: {len(tree)} controls")
        for t in tree[:50]:
            print(f"  d={t['d']:2d} {t['type']:14s} rect={t['rect']} name={t['name']!r}")
        OUT.write_text(json.dumps({"btn_idx": btn_idx, "title": new_dlg.window_text(), "tree": tree}, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        # 메인 윈도우 새 항목들 찾기
        print("\n(No modal dialog — main window 새 컨트롤 search)")
        tree = walk(win)
        # ListBox or Tree appeared?
        for t in tree:
            if t["type"] in ("ListBox","List","Tree","TreeItem","ListItem") and t["rect"][1] > 200:
                print(f"  d={t['d']:2d} {t['type']:14s} rect={t['rect']} name={t['name']!r}")
        OUT.write_text(json.dumps({"btn_idx": btn_idx, "tree": tree[:200]}, ensure_ascii=False, indent=2), encoding="utf-8")

    send_keys("{ESC}"); time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
