#!/usr/bin/env python3
"""Add Slave Device → Generic 선택 흐름.

probe_add_slave_dropdown 후속:
- DropDownPart [1] @ (361,85) 클릭 → 메뉴 등장
- "Generic" Text @ rect [388,353,495,369] 클릭 → 파일 다이얼로그
"""
import sys, time
from pathlib import Path
from pywinauto import mouse, Desktop
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common


def main():
    app, win = common.connect()
    common.ensure_maximized(win)
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)

    # Click 2nd DropDownPart (Add Slave Device)
    drops = []
    for b in win.descendants(control_type="Button"):
        try:
            n = b.window_text() or ""
            r = b.rectangle()
            if n == "DropDownPart" and r.top < 150:
                drops.append((b, r))
        except Exception: pass
    drops.sort(key=lambda x: x[1].left)
    if len(drops) < 2:
        print("FAIL: no 2nd dropdown"); return 1

    print("=== Open Add Slave Device dropdown ===")
    drops[1][0].click_input()
    time.sleep(1.5)

    # Find Generic Text and click
    print("=== Find 'Generic' Text ===")
    generic = None
    for t in win.descendants(control_type="Text"):
        try:
            n = t.window_text()
            if n == "Generic":
                generic = t; break
        except Exception: pass

    if generic is None:
        # ListItem 4 hover (idx 3, rect 315-392) — Generic은 4번째 카테고리에 있을 수 있음
        print("Generic Text 직접 못 찾음 — 4번째 ListItem hover 시도")
        mouse.move(coords=(450, 355)); time.sleep(1)
        for t in win.descendants(control_type="Text"):
            try:
                if t.window_text() == "Generic":
                    generic = t; break
            except Exception: pass

    if generic is None:
        print("FAIL: Generic 미발견"); send_keys("{ESC}"); return 1

    r = generic.rectangle()
    print(f"Generic rect=({r.left},{r.top},{r.right},{r.bottom}) — click")
    generic.click_input()
    time.sleep(2.5)

    # 파일 다이얼로그 detection
    print("\n=== After click — modal dialogs ===")
    for w in Desktop(backend="win32").windows():
        try:
            t = w.window_text() or ""
            if t and ("File" in t or "Open" in t or "Browse" in t or "Select" in t) and len(t) < 100:
                rect = w.rectangle()
                print(f"  [win32] {t!r} class={w.class_name()} rect={rect}")
        except Exception: pass

    print("\n=== ESC to cancel ===")
    send_keys("{ESC}"); time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
