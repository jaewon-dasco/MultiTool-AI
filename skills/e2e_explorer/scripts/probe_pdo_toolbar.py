#!/usr/bin/env python3
"""PDO 탭 toolbar 아이콘 식별 — Transmit PDOs/Receive PDOs 헤더 옆 Add/Remove 버튼.

가설:
  - "Transmit PDOs" Text 라벨 우측: Add Tx, Remove Tx 순
  - "Receive PDOs" Text 라벨 우측: Add Rx, Remove Rx 순
"""
import sys, time, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab


def main():
    app, win = common.connect()
    common.ensure_maximized(win)
    # PDO 탭 보장
    found_pdo = False
    for t in win.descendants(control_type="Text"):
        try:
            if t.window_text() == "Transmit PDOs":
                found_pdo = True; break
        except Exception: pass
    if not found_pdo:
        for t in win.descendants(control_type="TabItem"):
            try:
                if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
            except Exception: pass
        common.deselect_diagram(win); time.sleep(0.5)
        if not open_configure_panel(win, "CU_3606_21_1"): return 1
        time.sleep(1.5)
        if not click_left_tab(win, "PDO"): return 1
        time.sleep(2)

    # Transmit PDOs / Receive PDOs 헤더 위치
    headers = {}
    for t in win.descendants(control_type="Text"):
        try:
            n = t.window_text()
            if n in ("Transmit PDOs", "Receive PDOs"):
                r = t.rectangle()
                headers[n] = r
                print(f"Header {n!r}: rect=({r.left},{r.top},{r.right},{r.bottom})")
        except Exception: pass

    # 각 헤더 y범위에서 우측의 Button 추출
    print("\n=== Toolbar Buttons next to headers (좌→우 정렬) ===")
    for hname, hrect in headers.items():
        y_mid = (hrect.top + hrect.bottom) // 2
        btns = []
        for b in win.descendants(control_type="Button"):
            try:
                r = b.rectangle()
                if abs((r.top + r.bottom)//2 - y_mid) < 20 and r.left > hrect.right and r.left < hrect.right + 250 and r.width() < 50:
                    btns.append((b, r))
            except Exception: pass
        btns.sort(key=lambda x: x[1].left)
        print(f"\n  {hname}: {len(btns)} buttons")
        for i, (b, r) in enumerate(btns):
            name = b.window_text() or ''
            try: auto = b.automation_id()
            except: auto = ''
            print(f"    [{i}] rect=({r.left},{r.top},{r.right},{r.bottom}) name={name!r} auto_id={auto!r}")

    # 모든 Tooltip(HelpText) 시도
    print("\n=== Hover tooltip 확인 (각 button 위에 mouse 이동) ===")
    from pywinauto import mouse
    for hname, hrect in headers.items():
        y_mid = (hrect.top + hrect.bottom) // 2
        btns = []
        for b in win.descendants(control_type="Button"):
            try:
                r = b.rectangle()
                if abs((r.top + r.bottom)//2 - y_mid) < 20 and r.left > hrect.right and r.left < hrect.right + 250 and r.width() < 50:
                    btns.append((b, r))
            except Exception: pass
        btns.sort(key=lambda x: x[1].left)
        for i, (b, r) in enumerate(btns):
            cx, cy = (r.left + r.right)//2, (r.top + r.bottom)//2
            mouse.move(coords=(cx, cy))
            time.sleep(1.0)
            # 화면에 새로 등장한 ToolTip 찾기
            tip = None
            for tt in win.descendants(control_type="ToolTip"):
                try:
                    tn = tt.window_text()
                    if tn and tn.strip():
                        tip = tn; break
                except Exception: pass
            print(f"  {hname}[{i}] @({cx},{cy}) → tooltip={tip!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
