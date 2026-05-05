"""diag_sendkey.py — 단축키 1개 전송 후 윈도우/자식 변화 dump"""

import time
from pywinauto import Application, keyboard


def diag(ver: str = "8.4", keys: str = "^+n", label: str = "Ctrl+Shift+N"):
    exe = rf"C:\Program Files (x86)\Epec\MultiTool Creator {ver}\MultiTool.exe"
    app = Application(backend="uia").start(exe)

    deadline = time.time() + 60
    win = None
    while time.time() < deadline:
        time.sleep(2)
        for w in app.windows():
            n = w.element_info.name or ""
            if n and "DynamicSplashScreen" not in n \
                    and ("MultiTool" in n or "Creator" in n):
                win = w
                break
        if win:
            break
    if not win:
        print("[ERROR] 메인창 못 찾음")
        app.kill()
        return

    def dump_state(tag):
        print(f"\n=== {tag} ===")
        try:
            tops = list(app.windows())
        except Exception as e:
            tops = []
            print(f"  windows err: {e}")
        print(f"top-level windows: {len(tops)}")
        for w in tops:
            try:
                print(f"  - [{w.element_info.control_type}] '{w.element_info.name}'")
            except Exception:
                pass
        try:
            children = win.descendants(control_type="Window")
            print(f"main descendants Window: {len(children)}")
            for c in children[:20]:
                print(f"    - '{c.element_info.name}'")
        except Exception as e:
            print(f"  children err: {e}")

    print(f"main window: '{win.element_info.name}'")
    dump_state("BEFORE")

    win.set_focus()
    time.sleep(1)
    print(f"\n>>> sending {keys}  (label: {label})")
    keyboard.send_keys(keys, pause=0.1)
    time.sleep(3)

    dump_state("AFTER")

    time.sleep(2)
    try:
        app.kill()
    except Exception:
        pass


if __name__ == "__main__":
    import sys
    keys  = sys.argv[1] if len(sys.argv) > 1 else "^+n"
    label = sys.argv[2] if len(sys.argv) > 2 else "Ctrl+Shift+N"
    diag(keys=keys, label=label)
