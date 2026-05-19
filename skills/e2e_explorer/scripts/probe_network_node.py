#!/usr/bin/env python3
"""NETWORK 노드 클릭 후 BitRate 변경 UI 탐색.

가설:
  - Network Editor에서 NETWORK1을 Hyperlink로 클릭 → 노드 선택
  - 우측 패널 또는 floating toolbar에서 BitRate 속성 등장
  - BitRate ComboBox 또는 Edit 컨트롤 식별 가능
"""
import sys, json, time
from pathlib import Path
from pywinauto import mouse
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes import common

OUT = ROOT / "logs" / "probe_network_node.json"
TARGET_NETWORK = "NETWORK1"


def walk(ctrl, depth=0, out=None, limit=800):
    if out is None: out = []
    if len(out) >= limit: return out
    try:
        r = ctrl.rectangle()
        out.append({
            "depth": depth,
            "class": ctrl.class_name(),
            "name": (ctrl.window_text() or "")[:80],
            "ctrl_type": ctrl.element_info.control_type,
            "rect": [r.left, r.top, r.right, r.bottom],
        })
    except Exception: return out
    if depth > 20: return out
    try:
        for ch in ctrl.children():
            walk(ch, depth+1, out, limit)
    except Exception: pass
    return out


def find_network_hyperlink(win, name):
    for h in win.descendants(control_type="Hyperlink"):
        try:
            if h.window_text() == name:
                return h
        except Exception: pass
    return None


def main():
    app, win = common.connect()
    common.ensure_maximized(win)

    # Network Editor 화면으로 리셋 (이미 그렇겠지만)
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor":
                t.click_input(); time.sleep(1); break
        except Exception: pass
    common.deselect_diagram(win); time.sleep(0.5)

    print(f"=== Phase 0: baseline UIA tree (NETWORK 선택 전) ===")
    tree0 = walk(win)

    print(f"\n=== Phase 1: {TARGET_NETWORK} Hyperlink 클릭 ===")
    h = find_network_hyperlink(win, TARGET_NETWORK)
    if not h:
        print(f"FAIL: {TARGET_NETWORK} hyperlink not found")
        # dump available hyperlinks
        names = []
        for hh in win.descendants(control_type="Hyperlink"):
            try: names.append(hh.window_text())
            except Exception: pass
        print(f"Available Hyperlinks: {names[:20]}")
        return 1

    h.invoke()
    time.sleep(1.5)

    print("=== Phase 2: floating toolbar (kind='network') ===")
    fb = common.find_floating_toolbar_buttons(win, kind="network")
    print(f"Toolbar buttons: {len(fb)}")
    for i, b in enumerate(fb):
        try:
            r = b.rectangle()
            print(f"  [{i}] rect={r} name={b.window_text()!r}")
        except Exception: pass

    print("\n=== Phase 3: 선택 후 UIA 트리 (변경 부분) ===")
    tree1 = walk(win)
    # diff: new elements
    seen_rects = {(t["rect"][0], t["rect"][1], t["rect"][2], t["rect"][3]) for t in tree0 if "rect" in t}
    new_items = [t for t in tree1 if "rect" in t and tuple(t["rect"]) not in seen_rects]
    print(f"New elements appeared: {len(new_items)}")

    # BitRate 키워드 검색
    print("\n=== Phase 4: BitRate/Rate 관련 Text 찾기 ===")
    for t in tree1:
        n = t.get("name", "")
        if "rate" in n.lower() or "bit" in n.lower():
            print(f"  d={t['depth']} type={t['ctrl_type']:14s} name={n!r} rect={t.get('rect')}")

    print("\n=== Phase 5: 우측 패널 ComboBox/Edit 목록 ===")
    # x >= 1500 영역의 control들 (우측 패널 가정)
    forms = [t for t in tree1 if t.get("ctrl_type") in ("ComboBox", "Edit") and t.get("rect") and t["rect"][0] >= 1400]
    print(f"Right-panel forms: {len(forms)}")
    for f in forms[:20]:
        print(f"  d={f['depth']} {f['ctrl_type']:10s} rect={f['rect']} name={f.get('name')!r}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"new_items": new_items, "bitrate_hits": [t for t in tree1 if "rate" in (t.get("name") or "").lower() or "bit" in (t.get("name") or "").lower()],
                                "right_forms": forms}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
