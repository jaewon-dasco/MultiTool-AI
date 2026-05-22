#!/usr/bin/env python3
"""Network Editor 'Add Device' toolbar dropdown 동작 확인.

가설:
  - ButtonPart at (265,85) + DropDownPart at (300,85) — Split Button
  - DropDownPart 클릭 → 디바이스 모델 메뉴 등장
  - 메뉴에서 'CU_3606_21' 선택 → 디바이스 추가
"""
import sys, time, json
from pathlib import Path
from pywinauto import mouse, Desktop
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common


def walk(c, d=0, out=None, limit=300):
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

    # Find DropDownPart at expected positions (Add Device)
    drop_btns = []
    for b in win.descendants(control_type="Button"):
        try:
            n = b.window_text() or ""
            r = b.rectangle()
            if n == "DropDownPart" and r.top < 150:
                drop_btns.append((b, r))
        except Exception: pass
    drop_btns.sort(key=lambda x: x[1].left)
    print(f"DropDownPart buttons: {len(drop_btns)}")
    for i, (b, r) in enumerate(drop_btns):
        print(f"  [{i}] rect=({r.left},{r.top},{r.right},{r.bottom})")

    if not drop_btns:
        print("FAIL: no DropDownPart"); return 1

    # Click first DropDownPart
    print("\n=== Click first DropDownPart ===")
    btn, r = drop_btns[0]
    btn.click_input()
    time.sleep(1.5)

    tree1 = walk(win)
    new1 = [t for t in tree1 if "rect" in t and tuple(t["rect"]) not in seen0]
    print(f"New controls: {len(new1)}")
    # Menu/MenuItem
    for t in new1:
        if t["type"] in ("Menu", "MenuItem", "List", "ListItem", "ComboBox", "Window"):
            print(f"  d={t['d']:2d} {t['type']:12s} rect={t['rect']} name={t['name']!r}")

    # win32 dialog detection
    for w in Desktop(backend="win32").windows():
        try:
            t = w.window_text() or ""
            if t and "MultiTool" not in t and 10 < len(t) < 80 and "GDI+" not in t:
                # Filter very common windows
                if any(k in t for k in ["Add", "Device", "Select"]):
                    print(f"  [win32] {t!r}")
        except Exception: pass

    OUT = ROOT / "logs" / "probe_add_device_dropdown.json"
    OUT.write_text(json.dumps({"drop_buttons": len(drop_btns), "new_controls": new1[:80]}, ensure_ascii=False, indent=2), encoding="utf-8")

    send_keys("{ESC}"); time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
