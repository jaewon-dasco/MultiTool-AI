#!/usr/bin/env python3
"""io_pin recipe dry-run — 1.2 핀 모드 클릭만 단독 실행.

baseline 복원/저장/내보내기 없이 UI 액션만 검증.
"""
import sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import click_left_tab, open_configure_panel
from skills.e2e_explorer.recipes.io_pin_recipe import set_pin_mode, expand_connector


def main():
    app, win = common.connect()
    common.ensure_maximized(win)

    if not click_left_tab(win, "I/O"):
        from pywinauto.keyboard import send_keys
        send_keys("{ESC}"); time.sleep(0.3)
        for t in win.descendants(control_type="TabItem"):
            try:
                if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
            except Exception: pass
        common.deselect_diagram(win); time.sleep(0.5)
        if not open_configure_panel(win, "CU_3606_21_1"):
            print("FAIL: configure panel"); return 1
        time.sleep(1.5)
        if not click_left_tab(win, "I/O"):
            print("FAIL: I/O tab"); return 1
    time.sleep(2.0)

    print("=== expand_connector('1') ===")
    ok = expand_connector(win, "1")
    print(f"  ok={ok}")

    tests = [
        ("1.2", "DI"),
        ("1.7", "DO"),
        ("1.11", "AI"),
    ]
    for pin, mode in tests:
        print(f"\n=== set_pin_mode({pin}, {mode}) ===")
        r = set_pin_mode(win, pin_id=pin, mode_short=mode)
        for k, v in r.items():
            print(f"  {k}: {v}")
        time.sleep(1.0)

    return 0


if __name__ == "__main__":
    sys.exit(main())
