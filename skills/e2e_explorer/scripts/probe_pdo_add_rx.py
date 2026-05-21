#!/usr/bin/env python3
"""Probe: Add Rx 후 새 행의 UIA 속성 확인.

흐름:
1. MultiTool 연결 (이미 실행 중 가정, 아니면 시작)
2. Configure panel + PDO tab 진입
3. Rx 추가 전 baseline 스냅샷 (모든 DataItem/ListItem/Pane 위치)
4. pdo_add(Rx) 호출
5. 6초간 0.5초 폴링으로 트리 dump (10 스냅샷)
6. Receive PDOs 헤더 기준 추가된 컨트롤 식별 → logs/probe_pdo_add_rx.json
"""
import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "logs" / "probe_pdo_add_rx.json"


def snapshot_pdo_area(win, header_rect):
    """헤더 아래 영역의 모든 컨트롤 dump."""
    items = []
    types_to_scan = ["DataItem", "ListItem", "TreeItem", "Pane",
                     "Group", "Custom", "Text", "Button"]
    for t in types_to_scan:
        try:
            for c in win.descendants(control_type=t):
                try:
                    r = c.rectangle()
                    if (header_rect.bottom < r.top < header_rect.bottom + 600
                        and r.height() > 5 and r.left < 1500):
                        items.append({
                            "type": t,
                            "name": (c.window_text() or "")[:80],
                            "auto_id": getattr(c, "automation_id", lambda: "")(),
                            "rect": [r.left, r.top, r.right, r.bottom],
                            "size": [r.width(), r.height()],
                        })
                except Exception: pass
        except Exception: pass
    return items


def main():
    from skills.e2e_explorer.recipes import common
    from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab
    from skills.e2e_explorer.recipes.pdo_recipe import pdo_add, SECTIONS

    app, win = common.connect()
    common.ensure_maximized(win)

    print("Step 1: open Configure panel + PDO tab")
    if not open_configure_panel(win, "CU_3606_21_1"):
        print("FAIL: configure panel"); return 1
    time.sleep(1.0)
    if not click_left_tab(win, "PDO"):
        print("FAIL: PDO tab"); return 1
    time.sleep(1.5)

    print("Step 2: locate 'Receive PDOs' header")
    header_rect = None
    for t in win.descendants(control_type="Text"):
        try:
            if t.window_text() == SECTIONS["Rx"]:
                header_rect = t.rectangle(); break
        except Exception: pass
    if header_rect is None:
        print("FAIL: header"); return 1
    print(f"  header rect={header_rect}")

    print("Step 3: baseline snapshot (before Add)")
    before = snapshot_pdo_area(win, header_rect)
    print(f"  before: {len(before)} controls")

    print("Step 4: pdo_add(Rx)")
    add_res = pdo_add(win, "Rx")
    print(f"  add result: ok={add_res.get('ok')} action={add_res.get('action')}")
    if not add_res.get("ok"):
        OUT.write_text(json.dumps({"err": "pdo_add failed", "before": before, "add_res": add_res},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
        return 1

    print("Step 5: poll 12s (0.5s × 24) for new controls")
    snapshots = []
    for i in range(24):
        time.sleep(0.5)
        snap = snapshot_pdo_area(win, header_rect)
        snapshots.append({"t": (i+1)*0.5, "n_controls": len(snap),
                          "controls": snap})

    # Find new controls (not in before)
    before_keys = {(c["type"], tuple(c["rect"])) for c in before}
    final = snapshots[-1]["controls"]
    new_controls = [c for c in final if (c["type"], tuple(c["rect"])) not in before_keys]

    print(f"  before: {len(before)}, after: {len(final)}, NEW: {len(new_controls)}")
    print("\nNew controls (relative to baseline):")
    for c in new_controls[:20]:
        print(f"  {c['type']:10} rect={c['rect']} h={c['size'][1]:3} name={c['name'][:50]!r}")

    OUT.write_text(json.dumps({
        "header_rect": [header_rect.left, header_rect.top, header_rect.right, header_rect.bottom],
        "before": before,
        "after_final": final,
        "new_controls": new_controls,
        "snapshots_n": [s["n_controls"] for s in snapshots],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
