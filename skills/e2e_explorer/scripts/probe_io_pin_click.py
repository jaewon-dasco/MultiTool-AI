#!/usr/bin/env python3
"""I/O DataGrid의 행 클릭 후 변경된 UIA 트리 dump.

목표:
  1. DataItem(row=1)의 'Variable Name' 컬럼 셀 클릭 → Edit 진입 여부 확인
  2. 'Modes' 컬럼 셀 클릭 → ComboBox 펼침 여부 확인
  3. 클릭 전후 트리 차이 → 동적 컨트롤 식별
"""
import sys, json, time
from pathlib import Path
from pywinauto import mouse
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import click_left_tab, open_configure_panel

OUT = ROOT / "logs" / "probe_io_pin_click.json"


def walk(ctrl, depth=0, out=None, limit=500):
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
    except Exception as e:
        out.append({"depth": depth, "err": str(e)})
        return out
    if depth > 20: return out
    try:
        for ch in ctrl.children():
            walk(ch, depth+1, out, limit)
    except Exception: pass
    return out


def find_data_items(tree):
    """DataGrid 안의 DataItem 행들. 행 인덱스(name) 기준 정렬된 row rect 리스트 반환."""
    rows = []
    for t in tree:
        if t.get("ctrl_type") == "DataItem":
            r = t.get("rect", [])
            if len(r) == 4 and r[3] - r[1] > 5:  # 의미 있는 높이
                rows.append({"name": t.get("name", ""), "rect": r})
    # dedupe (같은 rect 반복 있음)
    seen = set(); out = []
    for r in rows:
        key = tuple(r["rect"])
        if key in seen: continue
        seen.add(key); out.append(r)
    out.sort(key=lambda r: r["rect"][1])
    return out


def find_headers(tree):
    """HeaderItem rect → 컬럼 x 범위 매핑."""
    cols = {}
    for t in tree:
        if t.get("ctrl_type") == "HeaderItem":
            n = t.get("name", "")
            r = t.get("rect", [])
            if n and len(r) == 4:
                cols[n] = (r[0], r[2])
    return cols


def main():
    app, win = common.connect()
    common.ensure_maximized(win)

    # Configure 패널이 아직 안 열려있을 수 있음 — 시도
    if not click_left_tab(win, "I/O"):
        print("I/O tab 실패, Configure 패널 진입 시도...")
        # Network Editor로 리셋
        send_keys("{ESC}"); time.sleep(0.3)
        for t in win.descendants(control_type="TabItem"):
            try:
                if t.window_text() == "Network Editor":
                    t.click_input(); time.sleep(1.0); break
            except Exception: pass
        common.deselect_diagram(win); time.sleep(0.5)
        if not open_configure_panel(win, "CU_3606_21_1"):
            print("FAIL: open_configure_panel"); return 1
        time.sleep(1.5)
        if not click_left_tab(win, "I/O"):
            print("FAIL: I/O tab after configure"); return 1
    time.sleep(2.0)

    print("=== Phase 1: baseline tree ===")
    tree0 = walk(win)
    rows = find_data_items(tree0)
    cols = find_headers(tree0)
    print(f"DataItems: {len(rows)} {[r['name'] for r in rows]}")
    print(f"Columns: {cols}")

    if not rows or "Variable Name" not in cols:
        print("FAIL: row/column 미발견")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"phase": "baseline_only", "rows": rows, "cols": cols, "tree": tree0}, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1

    # Phase 2: Variable Name 셀 클릭
    row0 = rows[0]
    vn_col = cols["Variable Name"]
    cx = (vn_col[0] + vn_col[1]) // 2
    cy = (row0["rect"][1] + row0["rect"][3]) // 2
    print(f"\n=== Phase 2: click Variable Name cell @({cx},{cy}) ===")
    mouse.click(coords=(cx, cy))
    time.sleep(1.0)
    tree1 = walk(win)
    # 더블클릭 시 Edit 진입 가능성
    print("=== Phase 2b: double-click ===")
    mouse.double_click(coords=(cx, cy))
    time.sleep(1.0)
    tree2 = walk(win)
    diff_2 = [t for t in tree2 if t.get("ctrl_type") == "Edit"]
    print(f"Edits after dbl-click: {len(diff_2)}")
    for e in diff_2[:10]:
        print(f"  rect={e['rect']} name={e['name']!r}")
    send_keys("{ESC}"); time.sleep(0.5)

    # Phase 3: Modes 셀 클릭
    if "Modes" in cols:
        m_col = cols["Modes"]
        mx = m_col[0] + 100  # 컬럼 좌측 끝에서 100px 안쪽
        print(f"\n=== Phase 3: click Modes cell @({mx},{cy}) ===")
        mouse.click(coords=(mx, cy))
        time.sleep(0.5)
        mouse.double_click(coords=(mx, cy))
        time.sleep(1.0)
        tree3 = walk(win)
        combos = [t for t in tree3 if t.get("ctrl_type") == "ComboBox"]
        print(f"ComboBoxes after Modes click: {len(combos)}")
        for c in combos[:10]:
            print(f"  rect={c['rect']} name={c['name']!r}")
        # 드롭다운 항목들 (List/ListItem)
        items = [t for t in tree3 if t.get("ctrl_type") == "ListItem"]
        print(f"ListItems present: {len(items)}")
        for it in items[:15]:
            print(f"  rect={it['rect']} name={it['name']!r}")
        send_keys("{ESC}"); time.sleep(0.5)
    else:
        tree3 = []

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "rows": rows, "cols": cols,
        "tree_after_var_click": tree1[-50:],
        "tree_after_var_dblclick": tree2[-50:],
        "tree_after_modes_click": tree3[-80:] if tree3 else [],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
