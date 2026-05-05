"""verify.py — 단축키 일괄 검증 및 shortcut_verified 갱신"""

import json
import time
from pathlib import Path

VERSIONS_DIR = Path(__file__).parent.parent.parent / "docs" / "versions"
DEMO_PROJECT = Path(__file__).parent.parent.parent / "DemoProject" / "ScanDemo" / "ScanDemo.mtproject"

DANGEROUS = {"Alt + F4"}  # 창 닫힘 — 검증 대상에서 제외


def _to_keys(sc: str) -> str:
    """'Ctrl + Shift + N' → '^+n' (pywinauto.keyboard syntax)"""
    parts = [p.strip() for p in sc.split("+")]
    mods  = {"Ctrl": "^", "Shift": "+", "Alt": "%"}
    out   = ""
    for p in parts:
        if p in mods:
            out += mods[p]
        elif p.upper().startswith("F") and p[1:].isdigit():
            out += "{" + p.upper() + "}"
        else:
            out += p.lower()
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
    return app.top_window()


def verify_shortcuts(ver: str):
    try:
        from pywinauto import Application, keyboard
    except ImportError:
        print("[ERROR] pywinauto 미설치")
        return

    fmap_path = VERSIONS_DIR / ver / "function_map.json"
    if not fmap_path.exists():
        print(f"[ERROR] function_map.json 없음: {fmap_path}")
        return

    fmap = json.loads(fmap_path.read_text(encoding="utf-8"))
    exe  = rf"C:\Program Files (x86)\Epec\MultiTool Creator {ver}\MultiTool.exe"
    app  = Application(backend="uia").start(exe)
    win  = _wait_main(app)

    # 데모 프로젝트를 명시 로드 → Save/Export 류 단축키 활성화
    if DEMO_PROJECT.exists():
        print(f"loading: {DEMO_PROJECT}")
        win.set_focus()
        time.sleep(1)
        keyboard.send_keys("^+o", pause=0.05)
        time.sleep(2)
        keyboard.send_keys(str(DEMO_PROJECT), pause=0.01, with_spaces=True)
        time.sleep(0.5)
        keyboard.send_keys("{ENTER}")
        time.sleep(8)
    else:
        print("[WARN] 데모 프로젝트 없음 — fresh 상태로 검증")

    def list_dialogs():
        names = set()
        try:
            for c in win.descendants(control_type="Window"):
                n = (c.element_info.name or "").strip()
                if n:
                    names.add(n)
        except Exception:
            pass
        try:
            for w in app.windows():
                n = (w.element_info.name or "").strip()
                if n and n != (win.element_info.name or "") \
                        and "DynamicSplashScreen" not in n:
                    names.add(n)
        except Exception:
            pass
        return names

    skipped = []
    for fn, info in fmap.items():
        sc = info.get("shortcut")
        if not sc:
            continue
        if sc in DANGEROUS:
            info["shortcut_verified"] = False
            skipped.append(fn)
            continue

        keys = _to_keys(sc)
        try:
            win.set_focus()
            time.sleep(0.3)
            before = list_dialogs()
            keyboard.send_keys(keys, pause=0.05)
            time.sleep(1.2)
            after = list_dialogs()
            new = after - before

            verified = bool(new)
            info["shortcut_verified"] = verified
            tag = "✓" if verified else "✗"
            print(f"  [{tag}] {fn} ({sc} → {keys})" + (f"  → {sorted(new)}" if new else ""))

            # 닫기
            keyboard.send_keys("{ESC}")
            time.sleep(0.4)
            keyboard.send_keys("{ESC}")
            time.sleep(0.4)
        except Exception as e:
            info["shortcut_verified"] = False
            print(f"  [!] {fn} ({sc}): {e}")

    fmap_path.write_text(
        json.dumps(fmap, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    try:
        app.kill()
    except Exception:
        pass

    total    = sum(1 for v in fmap.values() if v.get("shortcut"))
    verified = sum(1 for v in fmap.values() if v.get("shortcut_verified"))
    print(f"\n검증 완료: {verified}/{total} ({verified/total*100:.1f}%)")
    if skipped:
        print(f"위험 skip ({len(skipped)}): {skipped}")


if __name__ == "__main__":
    import sys
    ver = sys.argv[1] if len(sys.argv) > 1 else "8.4"
    verify_shortcuts(ver)
