#!/usr/bin/env python3
"""Network Editor toolbar — Add Device / Add Slave Device / Add Network 버튼 식별."""
import sys, time
from pathlib import Path

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

    # 상단 toolbar 영역 (y < 250)의 모든 Button + Hyperlink
    print("=== Button candidates (top region) ===")
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            n = b.window_text() or ""
            if r.top < 250 and r.width() < 200 and r.height() < 50:
                print(f"  Button rect=({r.left},{r.top},{r.right},{r.bottom}) name={n!r}")
        except Exception: pass

    print("\n=== Hyperlink candidates ===")
    for h in win.descendants(control_type="Hyperlink"):
        try:
            r = h.rectangle()
            n = h.window_text() or ""
            if r.top < 250:
                print(f"  Hyperlink rect=({r.left},{r.top},{r.right},{r.bottom}) name={n!r}")
        except Exception: pass

    print("\n=== Text labels (toolbar tooltips?) ===")
    for t in win.descendants(control_type="Text"):
        try:
            r = t.rectangle()
            n = t.window_text() or ""
            if r.top < 250 and r.left > 200 and 5 < r.height() < 30 and n and len(n) < 50:
                if any(k in n.lower() for k in ["add", "device", "network", "import", "export"]):
                    print(f"  Text rect=({r.left},{r.top},{r.right},{r.bottom}) name={n!r}")
        except Exception: pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
