#!/usr/bin/env python3
"""커넥터 '1' chevron 토글 — UIA Button 직접 click_input()/invoke() 시도.

이전 probe는 mouse.click(coords)로 시도했으나 효과 없음.
WPF RadTreeListView 토글은 UIA 요소에 직접 작용해야 할 수 있음.
"""
import sys, json, time
from pathlib import Path
from pywinauto import mouse
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import click_left_tab, open_configure_panel


def count_pin_rows(win):
    """현재 보이는 DataItem 행 개수."""
    rows = set()
    for d in win.descendants(control_type="DataItem"):
        try:
            r = d.rectangle()
            n = d.window_text()
            if r.height() > 5:
                rows.add((n, r.top, r.bottom))
        except Exception: pass
    return len(rows), sorted(set(n for n,_,_ in rows))


def find_connector1_button(win):
    """커넥터 '1' DataItem 영역(y≈107-130) 내의 좌측 작은 Button을 UIA 요소로 직접 반환."""
    target_y = 118
    candidates = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            if r.left >= 170 and r.right <= 230 and r.top <= target_y <= r.bottom and r.height() < 40:
                candidates.append((b, r))
        except Exception: pass
    # 가장 좌측의 좁은 버튼 선호
    candidates.sort(key=lambda x: (x[1].left, x[1].width()))
    return candidates[0] if candidates else (None, None)


def main():
    app, win = common.connect()
    common.ensure_maximized(win)

    if not click_left_tab(win, "I/O"):
        send_keys("{ESC}"); time.sleep(0.3)
        for t in win.descendants(control_type="TabItem"):
            try:
                if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
            except Exception: pass
        common.deselect_diagram(win); time.sleep(0.5)
        open_configure_panel(win, "CU_3606_21_1"); time.sleep(1.5)
        click_left_tab(win, "I/O")
    time.sleep(2.0)

    n0, rows0 = count_pin_rows(win)
    print(f"[0] baseline rows={n0}")

    btn, rect = find_connector1_button(win)
    if not btn:
        print("FAIL: connector chevron Button not found in UIA")
        return 1
    print(f"Found Button rect={rect}, class={btn.class_name()}")

    # 시도 1: click_input
    print("\n[1] btn.click_input()")
    try:
        btn.click_input()
        time.sleep(1.5)
    except Exception as e:
        print(f"  exception: {e}")
    n1, rows1 = count_pin_rows(win)
    print(f"  rows={n1} ({'COLLAPSED' if n1 < n0 else 'no change' if n1==n0 else 'EXPANDED'})")

    # 시도 2: invoke (만약 InvokePattern 지원하면)
    print("\n[2] btn.invoke()")
    try:
        if hasattr(btn, "invoke"):
            btn.invoke(); time.sleep(1.5)
        else:
            print("  invoke not supported")
    except Exception as e:
        print(f"  exception: {e}")
    n2, rows2 = count_pin_rows(win)
    print(f"  rows={n2}")

    # 시도 3: mouse.click_input via element rect center using pywinauto's wrapper
    print("\n[3] btn.click() (pywinauto wrapper)")
    try:
        btn.click(); time.sleep(1.5)
    except Exception as e:
        print(f"  exception: {e}")
    n3, rows3 = count_pin_rows(win)
    print(f"  rows={n3}")

    # 시도 4: 키보드 - 커넥터 row 선택 후 Left arrow (트리 collapse 표준 단축키)
    print("\n[4] DataItem '1' select_input() + Left arrow")
    for d in win.descendants(control_type="DataItem"):
        try:
            if d.window_text() == "1" and d.rectangle().height() > 5:
                d.click_input(); time.sleep(0.5)
                send_keys("{LEFT}"); time.sleep(1.5)
                break
        except Exception: pass
    n4, rows4 = count_pin_rows(win)
    print(f"  rows={n4}")

    # 시도 5: 다시 Right arrow → 펼침
    print("\n[5] Right arrow (expand)")
    send_keys("{RIGHT}"); time.sleep(1.5)
    n5, rows5 = count_pin_rows(win)
    print(f"  rows={n5}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
