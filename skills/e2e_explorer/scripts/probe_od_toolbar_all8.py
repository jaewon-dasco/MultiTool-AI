#!/usr/bin/env python3
"""OD toolbar 전체 8 버튼 + Pre-defined 다이얼로그 구조 probe."""
import sys, time, json
from pathlib import Path
from pywinauto import mouse, Desktop
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab

OUT = ROOT / "logs" / "probe_od_toolbar_all8.json"


def walk(c, d=0, out=None, limit=400):
    if out is None: out = []
    if len(out) >= limit: return out
    try:
        r = c.rectangle()
        out.append({"d": d, "type": c.element_info.control_type,
                    "name": (c.window_text() or "")[:80],
                    "rect": [r.left, r.top, r.right, r.bottom]})
    except Exception: return out
    if d > 18: return out
    try:
        for ch in c.children(): walk(ch, d+1, out, limit)
    except Exception: pass
    return out


def main():
    app, win = common.connect()
    common.ensure_maximized(win)
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor": t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)
    if not open_configure_panel(win, "CU_3606_21_1"): return 1
    time.sleep(1.5)
    if not click_left_tab(win, "Object Dictionary"): return 1
    time.sleep(2.0)

    # 더 넓은 x 범위 (260~900)로 toolbar 버튼 모두 수집
    print("=== OD toolbar Buttons (확장 검색 x=260-1000, y<200) ===")
    btns = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            if 260 < r.left < 1000 and 100 < r.top < 200 and r.width() < 80:
                btns.append((b, r))
        except Exception: pass
    btns.sort(key=lambda x: x[1].left)
    print(f"버튼 {len(btns)}개")
    for i, (b, r) in enumerate(btns):
        try:
            cn = b.class_name()
        except: cn = ''
        print(f"  [{i}] rect=({r.left},{r.top},{r.right},{r.bottom}) class={cn}")

    # Each button hover → tooltip
    print("\n=== Hover tooltip 캡쳐 (각 버튼 1.2초 대기) ===")
    tooltips = {}
    for i, (b, r) in enumerate(btns):
        cx, cy = (r.left+r.right)//2, (r.top+r.bottom)//2
        # 먼저 빈 영역으로 이동 (이전 tooltip 비우기)
        mouse.move(coords=(1000, 800))
        time.sleep(0.6)
        mouse.move(coords=(cx, cy))
        time.sleep(1.5)
        tip = None
        for tt in win.descendants(control_type="ToolTip"):
            try:
                tn = tt.window_text()
                if tn and tn.strip():
                    tip = tn; break
            except Exception: pass
        tooltips[i] = tip
        print(f"  [{i}] @({cx},{cy}) → {tip!r}")

    # Add Pre-defined Index 클릭 → 다이얼로그 구조
    pre_idx = None
    for i, tip in tooltips.items():
        if tip and "pre" in tip.lower():
            pre_idx = i; break
    if pre_idx is None and len(btns) >= 2:
        pre_idx = 1  # 사용자 정보: idx 1
        print(f"\n  Pre-defined tooltip 미감지 → 사용자 정보 idx=1 사용")

    if pre_idx is not None:
        print(f"\n=== Click Pre-defined Index button [{pre_idx}] ===")
        btn, r = btns[pre_idx]
        btn.click_input()
        time.sleep(2.0)

        # 다이얼로그 detection
        print("--- modal windows ---")
        for w in app.windows():
            try:
                t = w.window_text()
                if t and "MultiTool" not in t and len(t) < 100:
                    print(f"  app window: {t!r}")
            except Exception: pass

        # Walk current state
        tree = walk(win)
        # 새 다이얼로그 윈도우 탐색
        lists = [t for t in tree if t["type"] in ("List", "ListBox", "Tree", "DataGrid", "ListItem", "TreeItem")]
        print(f"\n--- List/Tree items ---: {len(lists)}")
        for t in lists[:30]:
            print(f"  d={t['d']:2d} {t['type']:12s} rect={t['rect']} name={t['name']!r}")

        OUT.write_text(json.dumps({"tooltips": tooltips, "tree_after_pre": tree[-100:]}, ensure_ascii=False, indent=2), encoding="utf-8")
        # ESC로 다이얼로그 닫기
        send_keys("{ESC}"); time.sleep(0.5)
    else:
        OUT.write_text(json.dumps({"tooltips": tooltips}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
