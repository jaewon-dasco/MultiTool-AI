#!/usr/bin/env python3
"""OD Pre-defined Index 다이얼로그 — 전체 흐름 + 트리 dump.

1. CU_3606_21_1 Configure 진입
2. Object Dictionary 탭 클릭
3. Pre-defined 버튼 찾아 클릭 (가능한 이름 변형 모두 시도)
4. 열린 다이얼로그 UIA 트리 dump
5. ESC로 다이얼로그 닫기
"""
import sys, time, json
from pathlib import Path
from pywinauto import Desktop
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import click_left_tab, open_configure_panel

OUT = ROOT / "logs" / "probe_od_dialog.json"


def walk(ctrl, depth=0, out=None, limit=500):
    if out is None: out = []
    if len(out) >= limit: return out
    try:
        r = ctrl.rectangle()
        out.append({"d": depth, "type": ctrl.element_info.control_type,
                    "name": (ctrl.window_text() or "")[:80],
                    "rect": [r.left, r.top, r.right, r.bottom]})
    except Exception: return out
    if depth > 18: return out
    try:
        for ch in ctrl.children(): walk(ch, depth+1, out, limit)
    except Exception: pass
    return out


def main():
    app, win = common.connect()
    common.ensure_maximized(win)

    # Reset → Network Editor → Configure panel
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)

    if not open_configure_panel(win, "CU_3606_21_1"):
        print("FAIL: configure panel"); return 1
    time.sleep(1.5)
    if not click_left_tab(win, "Object Dictionary"):
        print("FAIL: OD tab"); return 1
    time.sleep(2.0)

    # Find toolbar buttons in OD tab area
    print("=== Phase 1: OD 탭 toolbar Button 후보 ===")
    candidates = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            n = b.window_text() or ""
            # Toolbar 영역: y < 250 보통
            if r.top < 250 and r.height() < 50 and n:
                candidates.append((n, r.left, r.top, r.right, r.bottom))
        except Exception: pass
    candidates.sort(key=lambda c: c[1])
    for c in candidates[:30]:
        print(f"  {c[0]!r:35s} rect=({c[1]},{c[2]},{c[3]},{c[4]})")

    # "Pre-defined" 또는 "Predefined" 또는 "Add Pre" 포함 버튼 찾기
    pre_btn = None
    for b in win.descendants(control_type="Button"):
        try:
            n = (b.window_text() or "").lower()
            if "pre-defined" in n or "predefined" in n or "pre defined" in n:
                pre_btn = b
                print(f"\n=== Phase 2: 매칭 버튼 발견: {b.window_text()!r} ===")
                break
        except Exception: pass

    if pre_btn is None:
        # Hyperlink로도 시도
        for h in win.descendants(control_type="Hyperlink"):
            try:
                n = (h.window_text() or "").lower()
                if "pre-defined" in n or "predefined" in n:
                    pre_btn = h
                    print(f"\n=== Phase 2: Hyperlink 매칭: {h.window_text()!r} ===")
                    break
            except Exception: pass

    if pre_btn is None:
        print("FAIL: Pre-defined 버튼 없음")
        OUT.write_text(json.dumps({"od_buttons": candidates}, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1

    pre_btn.click_input()
    time.sleep(2.0)

    # 다이얼로그 찾기
    print("\n=== Phase 3: 열린 다이얼로그 ===")
    dlg = None
    for w in app.windows():
        try:
            t = w.window_text()
            if t and "MultiTool" not in t and len(t) < 100:
                dlg = w
                print(f"Dialog: {t!r}")
                break
        except Exception: pass

    tree = walk(dlg if dlg else win)
    print(f"Tree: {len(tree)} controls")

    # ListBox/Tree/ComboBox 후보
    print("\n=== Phase 4: 선택 가능 컨트롤 ===")
    for t in tree:
        if t["type"] in ("List", "Tree", "ListBox", "ComboBox", "DataGrid", "ListItem", "TreeItem"):
            print(f"  d={t['d']:2d} {t['type']:12s} rect={t['rect']} name={t['name']!r}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"od_buttons": candidates, "dialog_tree": tree}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")

    # 닫기
    send_keys("{ESC}"); time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
