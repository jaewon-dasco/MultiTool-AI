#!/usr/bin/env python3
"""OD 7 toolbar 버튼 idx 매핑 — 각 idx 클릭 후 등장 dialog 추적.

흐름:
1. Configure + OD tab
2. for idx in 0..6:
   - 활성 버튼인지 확인 (en=False면 skip)
   - baseline win32 windows
   - 클릭
   - after win32 windows
   - 새 dialog title 기록
   - ESC로 닫기
3. 결과 출력
"""
import sys, time, json
from pathlib import Path
from pywinauto import Desktop
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "logs" / "probe_od_map_idx.json"


def list_win32():
    out = []
    for w in Desktop(backend="win32").windows():
        try:
            t = w.window_text() or ""
            if t and "MultiTool Creator" not in t and 0 < len(t) < 100:
                out.append({"hwnd": w.handle, "title": t})
        except Exception: pass
    return out


def main():
    from skills.e2e_explorer.recipes import common
    from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab
    from skills.e2e_explorer.recipes.od_recipe import find_od_toolbar_buttons

    app, win = common.connect()
    common.ensure_maximized(win)

    print("Step 0: Network Editor tab")
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)

    print("Step 1: Configure + OD tab")
    if not open_configure_panel(win, "CU_3606_21_1"):
        print("FAIL: configure"); return 1
    time.sleep(1)
    if not click_left_tab(win, "Object Dictionary"):
        print("FAIL: OD tab"); return 1
    time.sleep(2)

    print("Step 2: map each idx")
    mapping = []
    for idx in range(7):
        # Re-fetch buttons each time (state may change)
        btns = find_od_toolbar_buttons(win)
        if idx >= len(btns):
            mapping.append({"idx": idx, "skipped": "out_of_range"})
            continue
        b, r = btns[idx]
        try:
            en = b.is_enabled()
        except Exception:
            en = None
        if not en:
            mapping.append({"idx": idx, "rect": [r.left,r.top,r.right,r.bottom],
                           "enabled": False, "dialog_title": None, "note": "disabled (row not selected)"})
            print(f"  idx={idx} en=False (skip click)")
            continue
        before = {w["hwnd"] for w in list_win32()}
        try:
            b.click_input()
            time.sleep(2.0)
        except Exception as e:
            mapping.append({"idx": idx, "click_error": str(e)})
            continue
        after = list_win32()
        new = [w for w in after if w["hwnd"] not in before]
        # Filter out 'Hidden Window'
        new = [w for w in new if w["title"] != "Hidden Window"]
        dialog_title = new[0]["title"] if new else None
        mapping.append({"idx": idx, "rect": [r.left,r.top,r.right,r.bottom],
                       "enabled": True, "dialog_title": dialog_title,
                       "new_count": len(new)})
        print(f"  idx={idx} en=True dialog={dialog_title!r}")
        # Dismiss with ESC
        if new:
            send_keys("{ESC}")
            time.sleep(1.0)
        time.sleep(0.5)

    print("\n=== OD toolbar idx → dialog mapping ===")
    for m in mapping:
        d = m.get("dialog_title")
        if d:
            print(f"  idx={m['idx']} → '{d}'")
        elif m.get("enabled") is False:
            print(f"  idx={m['idx']} → DISABLED (row select required)")
        else:
            print(f"  idx={m['idx']} → no dialog / {m.get('note','?')}")

    OUT.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
