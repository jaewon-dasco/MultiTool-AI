"""diag_shortcut.py — MenuItem UIA 프로퍼티 dump (단축키 노출 위치 진단)

FILE/PROJECT 메뉴를 펼쳐 각 MenuItem의 단축키 관련 프로퍼티를 모두 출력.
실행: py skills/fnscan/diag_shortcut.py [ver]
출력: skills/fnscan/diag_shortcut_result.json
"""

import json
import sys
import time
from pathlib import Path

EXE_PATTERN = r"C:\Program Files (x86)\Epec\MultiTool Creator {ver}\MultiTool.exe"
OUT_PATH    = Path(__file__).parent / "diag_shortcut_result.json"


def _get_label(elem) -> str:
    name = elem.element_info.name or ""
    if name and not name.startswith("MultiTool."):
        return name.split("\t")[0].strip()
    try:
        for child in elem.children(control_type="Text"):
            t = (child.element_info.name or "").strip()
            if t:
                return t
    except Exception:
        pass
    return ""


def _scan_uia(com_elem, prefix=""):
    out = {}
    for attr in ("CurrentAcceleratorKey", "CurrentAccessKey",
                 "CurrentHelpText", "CurrentItemStatus", "CurrentItemType"):
        try:
            v = getattr(com_elem, attr, None)
            if v:
                out[f"{prefix}{attr}"] = v
        except Exception:
            pass
    return out


def get_props(elem):
    info = elem.element_info
    out = {
        "name":          info.name or "",
        "label":         _get_label(elem),
        "automation_id": info.automation_id or "",
        "control_type":  info.control_type or "",
    }
    out.update(_scan_uia(info.element))

    try:
        legacy = elem.iface_legacy_iaccessible
        for attr in ("CurrentKeyboardShortcut", "CurrentDescription",
                     "CurrentDefaultAction"):
            try:
                v = getattr(legacy, attr, None)
                if v:
                    out[f"legacy.{attr}"] = v
            except Exception:
                pass
    except Exception:
        pass

    children_props = []
    try:
        for c in elem.children():
            cinfo = c.element_info
            cp = {
                "name":         cinfo.name or "",
                "control_type": cinfo.control_type or "",
            }
            cp.update(_scan_uia(cinfo.element))
            children_props.append(cp)
    except Exception:
        pass
    out["children"] = children_props
    return out


def _wait_main(app):
    deadline = time.time() + 60
    while time.time() < deadline:
        time.sleep(2)
        try:
            for w in app.windows():
                name = w.element_info.name or ""
                if name and "DynamicSplashScreen" not in name \
                        and ("MultiTool" in name or "Creator" in name):
                    time.sleep(2)
                    return w
        except Exception:
            pass
    print("[WARN] 메인창 대기 timeout — top_window fallback")
    return app.top_window()


def diag(ver: str = "8.4"):
    from pywinauto import Application, keyboard

    exe = EXE_PATTERN.format(ver=ver)
    app = Application(backend="uia").start(exe)
    win = _wait_main(app)
    win.set_focus()
    time.sleep(0.5)

    result = {}
    try:
        menus = win.descendants(control_type="Menu")
        if not menus:
            raise RuntimeError("Menu 컨트롤을 찾지 못함")
        top_items = menus[0].children(control_type="MenuItem")
    except Exception as e:
        print(f"[ERROR] 메뉴 탐색 실패: {e}")
        app.kill()
        return

    labeled = [(i, _get_label(i)) for i in top_items]
    print(f"top-level menus: {[(lbl or i.element_info.name) for i, lbl in labeled]}")
    targets = [(i, lbl) for i, lbl in labeled if lbl.upper() in ("FILE", "PROJECT")]
    print(f"targets: {[lbl for _, lbl in targets]}")

    for top, label in targets:
        win.set_focus()
        time.sleep(0.4)
        top.click_input()
        time.sleep(1.0)

        sub = []
        seen = set()
        try:
            for w in app.windows():
                try:
                    if w.element_info.control_type not in ("Window", "Popup", "Menu"):
                        continue
                    for mi in w.descendants(control_type="MenuItem"):
                        lbl = _get_label(mi)
                        if not lbl or lbl == label or lbl in seen:
                            continue
                        seen.add(lbl)
                        sub.append(get_props(mi))
                except Exception:
                    pass
        except Exception as e:
            print(f"[WARN] {label} popup 탐색 실패: {e}")

        result[label] = sub
        keyboard.send_keys("{ESC}")
        time.sleep(0.5)

    OUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"saved: {OUT_PATH}")
    for k, items in result.items():
        print(f"  [{k}] {len(items)} items")

    try:
        app.kill()
    except Exception:
        pass


if __name__ == "__main__":
    ver = sys.argv[1] if len(sys.argv) > 1 else "8.4"
    diag(ver)
