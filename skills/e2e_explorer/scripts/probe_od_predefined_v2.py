#!/usr/bin/env python3
"""OD Pre-defined Index inline panel probe v2.

흐름:
1. Configure panel + OD tab 진입 (확실히)
2. Baseline tree dump (열기 전)
3. OD toolbar idx=1 (Add Pre-defined) 클릭
4. 2s 대기 후 after dump
5. NEW controls 식별 → 인라인 패널 구조 파악
"""
import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "logs" / "probe_od_predefined_v2.json"


def walk(c, d=0, out=None, limit=800):
    if out is None: out = []
    if len(out) >= limit: return out
    try:
        r = c.rectangle()
        out.append({"d": d, "type": c.element_info.control_type,
                    "name": (c.window_text() or "")[:120],
                    "rect": [r.left, r.top, r.right, r.bottom]})
    except Exception: return out
    if d > 15: return out
    try:
        for ch in c.children(): walk(ch, d+1, out, limit)
    except Exception: pass
    return out


def main():
    from skills.e2e_explorer.recipes import common
    from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab
    from skills.e2e_explorer.recipes.od_recipe import click_od_toolbar_idx

    app, win = common.connect()
    common.ensure_maximized(win)

    print("Step 1: Configure panel + OD tab")
    if not open_configure_panel(win, "CU_3606_21_1"):
        print("FAIL: configure panel"); return 1
    time.sleep(1.0)
    if not click_left_tab(win, "Object Dictionary"):
        print("FAIL: OD tab"); return 1
    time.sleep(2.0)

    print("Step 2: baseline dump")
    before = walk(win)
    print(f"  baseline {len(before)} controls")
    before_keys = {(c["type"], tuple(c["rect"])) for c in before}

    print("Step 3: click OD toolbar idx=1 (Add Pre-defined)")
    r = click_od_toolbar_idx(win, idx=1, after_row_select=False)
    if not r.get("ok"):
        print(f"FAIL: {r}"); return 1
    print(f"  clicked: {r}")
    time.sleep(2.5)

    print("Step 4: after dump")
    after = walk(win)
    new_ctrls = [c for c in after if (c["type"], tuple(c["rect"])) not in before_keys]
    print(f"  after {len(after)} controls, NEW {len(new_ctrls)}")

    print("\nNEW controls (sorted by y):")
    new_ctrls.sort(key=lambda x: (x["rect"][1], x["rect"][0]))
    for c in new_ctrls:
        if c["type"] in ("Window","Dialog","Pane","Group","List","ListItem","TreeItem",
                          "ComboBox","Text","Button","DataItem","Custom","Edit","CheckBox"):
            name = c["name"]
            if name or c["type"] in ("Window","Dialog","List","ListItem","TreeItem","ComboBox","Edit"):
                print(f"  d={c['d']:2} {c['type']:10} rect={c['rect']} name={name[:80]!r}")

    OUT.write_text(json.dumps({
        "before_n": len(before), "after_n": len(after),
        "new_controls": new_ctrls,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")

    from pywinauto.keyboard import send_keys; send_keys("{ESC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
