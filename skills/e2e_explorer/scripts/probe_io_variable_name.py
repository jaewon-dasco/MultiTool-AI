#!/usr/bin/env python3
"""I/O 핀의 Variable Name 변경 경로 탐색.

시도 순서:
  1. Variable Name 셀에 우클릭 → context menu 확인
  2. 셀 더블클릭 → inline edit 진입 여부
  3. F2 키 → cell edit 진입
  4. 셀 단순 클릭 → 선택만 되는지

각 시도 후 UIA 트리 변화 dump.
"""
import sys, time, json
from pathlib import Path
from pywinauto import mouse
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import click_left_tab, open_configure_panel
from skills.e2e_explorer.recipes.io_pin_recipe import expand_connector, find_pin_row_rect

OUT = ROOT / "logs" / "probe_io_var_name.json"


def snapshot_tree(win, max_depth=15):
    out = []
    def walk(c, d=0):
        if d > max_depth: return
        try:
            r = c.rectangle()
            out.append({"d": d, "type": c.element_info.control_type,
                        "name": (c.window_text() or "")[:60],
                        "rect": [r.left, r.top, r.right, r.bottom]})
        except Exception: return
        try:
            for ch in c.children(): walk(ch, d+1)
        except Exception: pass
    walk(win)
    return out


def diff_trees(t0, t1):
    seen = {(t["rect"][0], t["rect"][1], t["rect"][2], t["rect"][3]) for t in t0 if "rect" in t}
    return [t for t in t1 if "rect" in t and tuple(t["rect"]) not in seen]


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
    if not click_left_tab(win, "I/O"):
        print("FAIL I/O tab"); return 1
    time.sleep(2)

    # Expand connector & target pin 1.2 (X1_2)
    expand_connector(win, "1")
    pin_rect = find_pin_row_rect(win, "1.2")
    if not pin_rect: print("FAIL pin 1.2"); return 1
    # Variable Name 컬럼 = x 284-418 (probe_io_pin_click 결과 기반)
    vn_cx = (284 + 418) // 2
    vn_cy = (pin_rect.top + pin_rect.bottom) // 2
    print(f"Variable Name cell @({vn_cx},{vn_cy})")

    tree_base = snapshot_tree(win)
    out = {"phases": []}

    # Phase 1: 우클릭
    print("\n=== Phase 1: Right click ===")
    mouse.right_click(coords=(vn_cx, vn_cy))
    time.sleep(1.0)
    tree1 = snapshot_tree(win)
    new1 = diff_trees(tree_base, tree1)
    menus = [t for t in new1 if t["type"] in ("Menu", "MenuItem", "MenuBar")]
    print(f"  New controls: {len(new1)}, MenuItems: {len(menus)}")
    for m in menus[:15]:
        print(f"    {m['type']:12s} name={m['name']!r} rect={m['rect']}")
    out["phases"].append({"action": "right_click", "new_controls": new1[:30], "menus": menus})
    send_keys("{ESC}"); time.sleep(0.5)

    # Phase 2: Double click
    print("\n=== Phase 2: Double click ===")
    mouse.double_click(coords=(vn_cx, vn_cy))
    time.sleep(1.0)
    tree2 = snapshot_tree(win)
    new2 = diff_trees(tree_base, tree2)
    edits = [t for t in new2 if t["type"] == "Edit"]
    print(f"  New Edits: {len(edits)}")
    for e in edits[:5]:
        print(f"    Edit rect={e['rect']} name={e['name']!r}")
    out["phases"].append({"action": "double_click", "new_controls": new2[:30], "edits": edits})
    send_keys("{ESC}"); time.sleep(0.5)

    # Phase 3: Single click + F2
    print("\n=== Phase 3: Click + F2 ===")
    mouse.click(coords=(vn_cx, vn_cy))
    time.sleep(0.5)
    send_keys("{F2}"); time.sleep(0.8)
    tree3 = snapshot_tree(win)
    new3 = diff_trees(tree_base, tree3)
    edits3 = [t for t in new3 if t["type"] == "Edit"]
    print(f"  After F2 new Edits: {len(edits3)}")
    for e in edits3[:5]:
        print(f"    Edit rect={e['rect']} name={e['name']!r}")
    out["phases"].append({"action": "click+F2", "new_controls": new3[:30], "edits": edits3})
    send_keys("{ESC}"); time.sleep(0.5)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
