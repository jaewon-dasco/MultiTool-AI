"""verify.py — 단축키 일괄 검증 및 shortcut_verified 갱신"""

import json
import time
from pathlib import Path

VERSIONS_DIR = Path(__file__).parent.parent.parent / "docs" / "versions"


def verify_shortcuts(ver: str):
    """shortcut 보유 항목마다 키 전송 → 다이얼로그 열림 여부로 verified 갱신"""
    try:
        from pywinauto import Application
    except ImportError:
        print("[ERROR] pywinauto 미설치")
        return

    fmap_path = VERSIONS_DIR / ver / "function_map.json"
    if not fmap_path.exists():
        print(f"[ERROR] function_map.json 없음: {fmap_path}")
        return

    fmap = json.loads(fmap_path.read_text(encoding="utf-8"))
    exe  = rf"C:\Program Files (x86)\Epec\MultiTool Creator {ver}\MultiToolCreator.exe"
    app  = Application(backend="uia").start(exe)
    time.sleep(3)
    win  = app.top_window()

    for fn, info in fmap.items():
        sc = info.get("shortcut")
        if not sc:
            continue
        win.set_focus()
        win.type_keys(sc, pause=0.3)
        time.sleep(0.5)
        try:
            dlg = app.top_window()
            verified = dlg.window_text() != win.window_text()
            info["shortcut_verified"] = verified
            if verified:
                dlg.close()
                time.sleep(0.3)
        except Exception:
            info["shortcut_verified"] = False

    fmap_path.write_text(json.dumps(fmap, ensure_ascii=False, indent=2), encoding="utf-8")
    app.kill()

    total    = sum(1 for v in fmap.values() if v.get("shortcut"))
    verified = sum(1 for v in fmap.values() if v.get("shortcut_verified"))
    print(f"검증 완료: {verified}/{total} ({verified/total*100:.1f}%)" if total else "단축키 없음")


if __name__ == "__main__":
    import sys
    ver = sys.argv[1] if len(sys.argv) > 1 else "8.4"
    verify_shortcuts(ver)
