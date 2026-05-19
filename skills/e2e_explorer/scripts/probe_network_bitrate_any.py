#!/usr/bin/env python3
"""Bit Rate 라벨 행의 모든 컨트롤 (모든 control_type)."""
import sys, time
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common


def main():
    app, win = common.connect()
    common.ensure_maximized(win)
    # 선택 가정 — 이전 probe 후 상태 유지된 듯
    label_rect = None
    for t in win.descendants(control_type="Text"):
        try:
            if t.window_text().strip() == "Bit Rate":
                label_rect = t.rectangle(); break
        except Exception: pass
    if not label_rect:
        # Re-select NETWORK1
        for h in win.descendants(control_type="Hyperlink"):
            try:
                if h.window_text() == "NETWORK1": h.invoke(); time.sleep(1.5); break
            except Exception: pass
        for t in win.descendants(control_type="Text"):
            try:
                if t.window_text().strip() == "Bit Rate":
                    label_rect = t.rectangle(); break
            except Exception: pass
    print(f"Bit Rate label: {label_rect}")
    y_mid = (label_rect.top + label_rect.bottom) // 2

    by_type = Counter()
    matches = []
    for d in win.descendants():
        try:
            r = d.rectangle()
            if abs((r.top + r.bottom)//2 - y_mid) < 25 and r.left > label_rect.right - 30 and r.left < 800 and r.width() > 5 and r.height() > 5:
                ct = d.element_info.control_type
                by_type[ct] += 1
                matches.append((ct, r.left, r.top, r.right, r.bottom, (d.window_text() or "")[:40]))
        except Exception: pass

    print(f"All controls near Bit Rate row: {len(matches)}")
    print(f"by type: {dict(by_type)}")
    matches.sort(key=lambda m: m[1])
    for m in matches[:30]:
        print(f"  {m[0]:14s} rect=({m[1]},{m[2]},{m[3]},{m[4]}) name={m[5]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
