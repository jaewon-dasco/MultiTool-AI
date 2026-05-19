#!/usr/bin/env python3
"""I/O 패널 UIA 트리 dump — OCR이 안 잡는 Edit 셀/표 데이터 확인.

이미 Configure 패널이 열려있을 가능성 → 우선 Network Editor로 리셋한 뒤 재진입."""
import sys, json, time
from pathlib import Path
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes import common
from skills.e2e_explorer.recipes.field_change import open_configure_panel, click_left_tab

OUT = ROOT / "logs" / "probe_io_uia.json"


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
    except Exception as e:
        out.append({"depth": depth, "err": str(e)})
        return out
    if depth > 20: return out
    try:
        for ch in ctrl.children():
            walk(ch, depth+1, out, limit)
    except Exception: pass
    return out


def reset_to_network_editor(win):
    """Network Editor 탭으로 돌아가서 깨끗한 상태."""
    send_keys("{ESC}"); time.sleep(0.3)
    for t in win.descendants(control_type="TabItem"):
        try:
            if t.window_text() == "Network Editor":
                t.click_input(); time.sleep(1.0); return True
        except Exception: pass
    return False


def main():
    app, win = common.connect()
    common.ensure_maximized(win)

    # 우선 Network Editor로 리셋
    reset_to_network_editor(win)
    common.deselect_diagram(win)
    time.sleep(0.5)

    if not open_configure_panel(win, "CU_3606_21_1"):
        print("FAIL: open Configure panel — 디바이스 hyperlink 못 찾음")
        # Configure 이미 열려있을 수 있으니 그대로 진행해보기
        print("Try: skip configure open, attempt I/O tab directly")
    time.sleep(1.5)

    if not click_left_tab(win, "I/O"):
        print("FAIL: I/O tab"); return 1
    time.sleep(2.5)

    tree = walk(win)
    print(f"Total controls: {len(tree)}")

    from collections import Counter
    by_type = Counter(t["ctrl_type"] for t in tree if "ctrl_type" in t)
    print("By control_type:", dict(by_type))

    targets = ["VAVLE", "VALVE", "LED", "X1_", "SW_"]
    hits = [t for t in tree if any(k in (t.get("name") or "") for k in targets)]
    print(f"\nUIA hits (변수명 포함): {len(hits)}")
    for h in hits[:20]:
        print(f"  d={h['depth']} type={h['ctrl_type']:20s} name={h['name']!r}")

    forms = [t for t in tree if t.get("ctrl_type") in ("Edit", "ComboBox")]
    print(f"\nEdit/ComboBox: {len(forms)}")
    for f in forms[:25]:
        print(f"  d={f['depth']} type={f['ctrl_type']:10s} name={f['name']!r} rect={f.get('rect')}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"total": len(tree), "by_type": dict(by_type),
                                "tree": tree}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDump: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
