#!/usr/bin/env python3
"""OD toolbar 6 unnamed Button — 각 버튼의 AutomationId/ClassName/HelpText 추출."""
import sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import click_left_tab, open_configure_panel


def main():
    app, win = common.connect()
    common.ensure_maximized(win)
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)
    if not open_configure_panel(win, "CU_3606_21_1"): return 1
    time.sleep(1.2)
    if not click_left_tab(win, "Object Dictionary"): return 1
    time.sleep(2)

    targets = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            if 260 < r.left < 600 and 110 < r.top < 170 and r.width() < 80:
                targets.append(b)
        except Exception: pass
    targets.sort(key=lambda b: b.rectangle().left)

    print(f"OD toolbar buttons: {len(targets)}")
    for i, b in enumerate(targets):
        r = b.rectangle()
        info = {}
        for attr in ("automation_id", "class_name"):
            try: info[attr] = getattr(b, attr)()
            except Exception: pass
        # HelpText / LegacyIAccessibleDescription via element_info
        try:
            ei = b.element_info
            info["help_text"] = ei.rich_text if hasattr(ei, "rich_text") else None
        except Exception: pass
        # Try ToolTip via accessibility info — use AccessibleObjectFromWindow not trivial. Skip.
        print(f"  [{i}] rect=({r.left},{r.top},{r.right},{r.bottom}) auto_id={info.get('automation_id')!r} class={info.get('class_name')!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
