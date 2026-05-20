#!/usr/bin/env python3
"""Network Editor 'Add Slave Device' DropDown 메뉴 구조.

probe_net_toolbar 결과:
  - ButtonPart + DropDownPart at (265,85) — Add Device
  - ButtonPart + DropDownPart at (326,85) — Add Slave Device (가설)
DropDownPart 클릭 → 메뉴 등장. Generic 옵션 + 등록된 슬레이브 디바이스 리스트.
"""
import sys, time, json
from pathlib import Path
from pywinauto import mouse, Desktop
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common


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
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)

    # baseline tree
    tree0 = walk(win)
    seen0 = {(t["rect"][0], t["rect"][1], t["rect"][2], t["rect"][3]) for t in tree0 if "rect" in t}

    # Find 2nd DropDownPart (Add Slave Device 가설)
    drops = []
    for b in win.descendants(control_type="Button"):
        try:
            n = b.window_text() or ""
            r = b.rectangle()
            if n == "DropDownPart" and r.top < 150:
                drops.append((b, r))
        except Exception: pass
    drops.sort(key=lambda x: x[1].left)
    print(f"DropDownPart 개수: {len(drops)}")
    for i, (b, r) in enumerate(drops):
        print(f"  [{i}] rect=({r.left},{r.top},{r.right},{r.bottom})")

    if len(drops) < 2:
        print("Add Slave Device dropdown not found"); return 1

    target = drops[1]  # 2nd dropdown = Add Slave Device
    print(f"\n=== Click 2nd DropDownPart (Add Slave Device) ===")
    btn, r = target
    btn.click_input()
    time.sleep(1.5)

    tree1 = walk(win)
    new1 = [t for t in tree1 if "rect" in t and tuple(t["rect"]) not in seen0]
    print(f"새 컨트롤: {len(new1)}")

    # MenuItem / ListItem 추출 (메뉴 항목들)
    menus = [t for t in new1 if t["type"] in ("MenuItem", "ListItem", "Menu", "List", "Window")]
    print(f"메뉴/아이템: {len(menus)}")
    for m in menus[:30]:
        print(f"  d={m['d']:2d} {m['type']:12s} rect={m['rect']} name={m['name']!r}")

    # Generic 키워드 검색
    print("\n=== 'Generic' 키워드 검색 ===")
    for t in new1:
        if "generic" in (t.get("name") or "").lower():
            print(f"  d={t['d']} {t['type']:12s} rect={t['rect']} name={t['name']!r}")

    OUT = ROOT / "logs" / "probe_add_slave_dropdown.json"
    OUT.write_text(json.dumps({"drops_count": len(drops), "new_controls": new1[:80]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")

    send_keys("{ESC}"); time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
