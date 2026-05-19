#!/usr/bin/env python3
"""Diagnostics 탭 UIA tree dump — DataGrid 행/열 구조."""
import sys, time, json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab

OUT = ROOT / "logs" / "probe_diagnostics_uia.json"


def walk(c, d=0, out=None, limit=400):
    if out is None: out = []
    if len(out) >= limit: return out
    try:
        r = c.rectangle()
        out.append({"d": d, "type": c.element_info.control_type,
                    "name": (c.window_text() or "")[:80],
                    "rect": [r.left, r.top, r.right, r.bottom]})
    except Exception: return out
    if d > 18: return out
    try:
        for ch in c.children(): walk(ch, d+1, out, limit)
    except Exception: pass
    return out


def main():
    app, win = common.connect()
    common.ensure_maximized(win)
    # 가정: probe_diagnostics 이후 상태 — Diagnostics 탭이 이미 열려있음
    # 안전을 위해 reload
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)
    if not open_configure_panel(win, "CU_3606_21_1"):
        print("FAIL configure"); return 1
    time.sleep(1.5)
    if not click_left_tab(win, "Diagnostics"):
        print("FAIL Diagnostics"); return 1
    time.sleep(2.5)

    tree = walk(win)
    by_type = Counter(t["type"] for t in tree if "type" in t)
    print(f"Total controls: {len(tree)}")
    print(f"By type: {dict(by_type)}")

    # DataGrid + Header + DataItem 탐색
    print("\n=== DataGrid / Header / DataItem ===")
    for t in tree:
        if t["type"] in ("DataGrid", "Header", "HeaderItem", "DataItem"):
            ind = '  ' * t["d"]
            print(f"  d={t['d']:2d} {t['type']:14s} rect={t['rect']} name={t['name']!r}")

    # Edit / ComboBox - 셀 편집 컨트롤?
    print("\n=== Edit / ComboBox / CheckBox in main area ===")
    for t in tree:
        if t["type"] in ("Edit", "ComboBox", "CheckBox") and t.get("rect"):
            r = t["rect"]
            if r[0] > 200 and r[1] < 1000:
                print(f"  d={t['d']:2d} {t['type']:10s} rect={r} name={t['name']!r}")

    # Text labels - 행 식별자 (Temperature, SupplyVoltage, Ref5V, CycleTime)
    print("\n=== Text labels (Temperature/SupplyVoltage/Ref5V/CycleTime) ===")
    targets = ["temperature", "supply", "ref5", "cycle"]
    for t in tree:
        if t["type"] == "Text" and t.get("name"):
            nm = t["name"].lower()
            if any(k in nm for k in targets):
                print(f"  d={t['d']:2d} rect={t['rect']} name={t['name']!r}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"total": len(tree), "by_type": dict(by_type), "tree": tree}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
