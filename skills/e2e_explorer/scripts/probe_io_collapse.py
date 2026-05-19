#!/usr/bin/env python3
"""커넥터 노드(1) 클릭으로 핀 리스트 expand/collapse 동작 확인.

가설:
  - DataItem 'name=1'은 커넥터 1 부모 노드, '1.1'~'1.32'는 자식 핀 노드
  - 좌측 작은 Button(rect width ~22px @ x=195)은 tree expand/collapse 토글
  - 커넥터 노드 행 또는 토글 버튼 클릭으로 펼침/접힘 가능
"""
import sys, json, time
from pathlib import Path
from pywinauto import mouse
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import click_left_tab, open_configure_panel

OUT = ROOT / "logs" / "probe_io_collapse.json"


def walk(ctrl, depth=0, out=None, limit=600):
    if out is None: out = []
    if len(out) >= limit: return out
    try:
        r = ctrl.rectangle()
        out.append({
            "depth": depth,
            "class": ctrl.class_name(),
            "name": (ctrl.window_text() or "")[:80],
            "ctrl_type": ctrl.element_info.control_type,
            "rect": [r.left, r.top, r.right, r.bottom],
        })
    except Exception: return out
    if depth > 20: return out
    try:
        for ch in ctrl.children():
            walk(ch, depth+1, out, limit)
    except Exception: pass
    return out


def pin_rows(tree):
    """DataItem name 추출 (dedupe)."""
    seen = {}
    for t in tree:
        if t.get("ctrl_type") == "DataItem":
            n = t.get("name", "")
            r = tuple(t.get("rect", []))
            if r not in seen and len(r) == 4 and r[3]-r[1] > 5:
                seen[r] = n
    return [seen[r] for r in sorted(seen.keys(), key=lambda x: x[1])]


def find_connector_row(tree, name="1"):
    """DataItem name='1' (커넥터 부모) 좌표."""
    for t in tree:
        if t.get("ctrl_type") == "DataItem" and t.get("name") == name:
            r = t.get("rect")
            if r and r[3]-r[1] > 5:
                return r
    return None


def find_expand_button_near(tree, row_rect):
    """row와 같은 y, x<220 위치의 작은 Button (tree chevron)."""
    y_mid = (row_rect[1] + row_rect[3]) // 2
    for t in tree:
        if t.get("ctrl_type") != "Button": continue
        r = t.get("rect", [])
        if len(r) != 4: continue
        if r[0] >= 175 and r[2] <= 220 and r[1] <= y_mid <= r[3]:
            return r
    return None


def main():
    app, win = common.connect()
    common.ensure_maximized(win)

    if not click_left_tab(win, "I/O"):
        send_keys("{ESC}"); time.sleep(0.3)
        for t in win.descendants(control_type="TabItem"):
            try:
                if t.window_text() == "Network Editor":
                    t.click_input(); time.sleep(1); break
            except Exception: pass
        common.deselect_diagram(win); time.sleep(0.5)
        if not open_configure_panel(win, "CU_3606_21_1"):
            print("FAIL: configure"); return 1
        time.sleep(1.5)
        if not click_left_tab(win, "I/O"):
            print("FAIL: I/O tab"); return 1
    time.sleep(2.0)

    print("=== Phase 0: baseline (expanded) ===")
    tree0 = walk(win)
    rows0 = pin_rows(tree0)
    print(f"rows: {len(rows0)} → {rows0}")
    conn_rect = find_connector_row(tree0, "1")
    print(f"connector '1' rect: {conn_rect}")
    chev_rect = find_expand_button_near(tree0, conn_rect) if conn_rect else None
    print(f"expand button rect: {chev_rect}")

    if not conn_rect:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"phase": "no_connector_row", "rows": rows0}, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1

    # Phase 1: 커넥터 행 (text) 클릭 → 접힘 시도
    cx_text = (conn_rect[0] + conn_rect[2]) // 2
    cy_text = (conn_rect[1] + conn_rect[3]) // 2
    print(f"\n=== Phase 1: row text click @({cx_text},{cy_text}) ===")
    mouse.click(coords=(cx_text, cy_text))
    time.sleep(1.0)
    tree1 = walk(win)
    rows1 = pin_rows(tree1)
    print(f"rows: {len(rows1)} → {rows1[:10]}...")

    # Phase 2: chevron(전용 토글) 클릭
    if chev_rect:
        cx_chev = (chev_rect[0] + chev_rect[2]) // 2
        cy_chev = (chev_rect[1] + chev_rect[3]) // 2
        print(f"\n=== Phase 2: chevron click @({cx_chev},{cy_chev}) ===")
        mouse.click(coords=(cx_chev, cy_chev))
        time.sleep(1.0)
        tree2 = walk(win)
        rows2 = pin_rows(tree2)
        print(f"rows: {len(rows2)} → {rows2[:10]}...")

        # Phase 3: 다시 클릭 (펼침 복원)
        mouse.click(coords=(cx_chev, cy_chev))
        time.sleep(1.0)
        tree3 = walk(win)
        rows3 = pin_rows(tree3)
        print(f"\n=== Phase 3: chevron re-click → rows: {len(rows3)} → {rows3[:10]}...")
    else:
        rows2 = rows3 = None

    # Phase 4: double-click 커넥터 행
    print(f"\n=== Phase 4: double-click connector row @({cx_text},{cy_text}) ===")
    mouse.double_click(coords=(cx_text, cy_text))
    time.sleep(1.0)
    tree4 = walk(win)
    rows4 = pin_rows(tree4)
    print(f"rows: {len(rows4)} → {rows4[:10]}...")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "baseline_rows": rows0,
        "after_row_click_rows": rows1,
        "after_chev_click_rows": rows2,
        "after_chev_reclick_rows": rows3,
        "after_row_dblclick_rows": rows4,
        "connector_rect": conn_rect,
        "chevron_rect": chev_rect,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
