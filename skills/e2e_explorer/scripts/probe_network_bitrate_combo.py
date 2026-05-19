#!/usr/bin/env python3
"""NETWORK1 선택 후 Bit Rate 라벨 인접 ComboBox 찾기."""
import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes import common

OUT = ROOT / "logs" / "probe_network_bitrate_combo.json"


def main():
    app, win = common.connect()
    common.ensure_maximized(win)

    # NETWORK1 선택 (이미 선택된 상태라면 skip)
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)

    for h in win.descendants(control_type="Hyperlink"):
        try:
            if h.window_text() == "NETWORK1":
                h.invoke(); time.sleep(1.5); break
        except Exception: pass

    # Bit Rate 라벨 y 범위 (≈265-282)
    label_rect = None
    for t in win.descendants(control_type="Text"):
        try:
            if t.window_text().strip() == "Bit Rate":
                label_rect = t.rectangle()
                break
        except Exception: pass

    if not label_rect:
        print("FAIL: Bit Rate label not found"); return 1
    print(f"Bit Rate label rect: {label_rect}")

    y_mid = (label_rect.top + label_rect.bottom) // 2
    print(f"y_mid: {y_mid}")

    # 같은 row, x > 230 (label 우측)의 ComboBox/Edit 후보
    candidates = []
    for ctrl_type in ("ComboBox", "Edit"):
        for c in win.descendants(control_type=ctrl_type):
            try:
                r = c.rectangle()
                if abs((r.top + r.bottom)//2 - y_mid) < 30 and r.left > label_rect.right - 50 and r.left < 800:
                    candidates.append({
                        "type": ctrl_type, "rect": [r.left, r.top, r.right, r.bottom],
                        "name": c.window_text(),
                        "x_dist_from_label_right": r.left - label_rect.right,
                    })
            except Exception: pass

    print(f"Adjacent control candidates: {len(candidates)}")
    for c in candidates:
        print(f"  {c['type']:10s} rect={c['rect']} dist={c['x_dist_from_label_right']:>4} name={c['name']!r}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"label_rect": [label_rect.left, label_rect.top, label_rect.right, label_rect.bottom],
                                "candidates": candidates}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
