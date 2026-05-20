#!/usr/bin/env python3
"""Probe MultiTool 'Add Pre-defined' OD dialog.

흐름:
  1. MultiTool 연결 (이미 띄워져 있어야 함)
  2. Device Configure 패널 진입 → Object Dictionary 탭 클릭
  3. Toolbar 'Add Pre-defined' 버튼 클릭
  4. 열린 다이얼로그의 UI 트리 dump → logs/probe_od_predefined.json
  5. ESC로 다이얼로그 닫기

산출: logs/probe_od_predefined.json — D_od#31 시드 dialog 필드 설계 입력.
"""
import sys, time, json
from pathlib import Path
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab

DEVICE = "CU_3606_21_1"
TAB = "Object Dictionary"
TOOLBAR_LABEL = "Add Pre-defined"
OUT = ROOT / "logs" / "probe_od_predefined.json"
TREE_LIMIT = 800  # 인라인 패널 전체 캡처용 상향


def walk(ctrl, depth=0, out=None, limit=TREE_LIMIT):
    if out is None: out = []
    if len(out) >= limit: return out
    try:
        r = ctrl.rectangle()
        out.append({
            "depth": depth,
            "class": ctrl.class_name(),
            "name": ctrl.window_text()[:80],
            "auto_id": getattr(ctrl, "automation_id", lambda: "")(),
            "ctrl_type": ctrl.element_info.control_type,
            "rect": [r.left, r.top, r.right, r.bottom],
        })
    except Exception as e:
        out.append({"depth": depth, "err": str(e)})
        return out
    if depth > 12: return out
    try:
        for ch in ctrl.children():
            walk(ch, depth+1, out, limit)
    except Exception:
        pass
    return out


def find_dialog(app, title_keywords=("Pre-defined", "Predefined", "Add")):
    """새로 열린 modal 다이얼로그 탐색."""
    for w in app.windows():
        try:
            t = w.window_text()
            if any(k.lower() in t.lower() for k in title_keywords):
                return w
        except Exception: pass
    return None


def click_toolbar_button(win, label: str) -> bool:
    """툴바에서 텍스트 라벨 일치하는 버튼 클릭."""
    for b in win.descendants(control_type="Button"):
        try:
            if b.window_text().strip() == label:
                b.click_input(); return True
        except Exception: pass
    # 텍스트가 없으면 가까운 Text 라벨로 fallback
    for t in win.descendants(control_type="Text"):
        try:
            if t.window_text().strip() == label:
                t.click_input(); return True
        except Exception: pass
    return False


def main():
    app, win = common.connect()
    common.ensure_maximized(win)

    if not open_configure_panel(win, DEVICE):
        print("FAIL: open Configure panel"); return 1
    time.sleep(1.0)

    if not click_left_tab(win, TAB):
        print(f"FAIL: tab '{TAB}'"); return 1
    time.sleep(1.5)

    # OD toolbar 버튼은 name 비어있어 라벨 fallback 불가 → od_recipe idx 1 사용 (선택 전 = Add Pre-defined)
    from skills.e2e_explorer.recipes.od_recipe import click_od_toolbar_idx
    r = click_od_toolbar_idx(win, idx=1, after_row_select=False)
    if not r.get("ok"):
        print(f"FAIL: od_toolbar[1] click — {r.get('action')}"); return 1
    print(f"clicked OD toolbar idx=1 (Add Pre-defined)")
    time.sleep(2.0)

    dlg = find_dialog(app)
    if not dlg:
        # main window 안의 popup일 수도 있음 — 최근 추가된 Pane/Window 자식 탐색
        print("WARN: top-level dialog not found, dumping main window children")
        tree = walk(win)
    else:
        print(f"Dialog found: {dlg.window_text()}")
        tree = walk(dlg)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Tree dumped: {OUT} ({len(tree)} controls)")

    # 닫기
    send_keys("{ESC}"); time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
