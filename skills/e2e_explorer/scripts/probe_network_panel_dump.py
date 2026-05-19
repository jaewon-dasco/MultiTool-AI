#!/usr/bin/env python3
"""NETWORK1 선택 후 좌측 패널(x<800) 전체 dump."""
import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common

OUT = ROOT / "logs" / "probe_network_panel.json"


def walk(ctrl, depth=0, out=None, limit=800):
    if out is None: out = []
    if len(out) >= limit: return out
    try:
        r = ctrl.rectangle()
        out.append({"d": depth, "type": ctrl.element_info.control_type,
                    "name": (ctrl.window_text() or "")[:60],
                    "rect": [r.left, r.top, r.right, r.bottom]})
    except Exception: return out
    if depth > 20: return out
    try:
        for ch in ctrl.children(): walk(ch, depth+1, out, limit)
    except Exception: pass
    return out


def main():
    app, win = common.connect()
    common.ensure_maximized(win)
    # NETWORK1 선택
    for h in win.descendants(control_type="Hyperlink"):
        try:
            if h.window_text() == "NETWORK1": h.invoke(); time.sleep(1.5); break
        except Exception: pass

    tree = walk(win)
    # 좌측 패널 (x<800, y 200~700)
    left_panel = [t for t in tree if t.get("rect") and t["rect"][0] < 800 and 200 < t["rect"][1] < 700 and t["rect"][2] - t["rect"][0] > 5]
    print(f"Left panel controls (x<800, 200<y<700): {len(left_panel)}")
    left_panel.sort(key=lambda t: (t["rect"][1], t["rect"][0]))
    for t in left_panel:
        print(f"  d={t['d']:2d} {t['type']:14s} rect={t['rect']} name={t['name']!r}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(left_panel, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
