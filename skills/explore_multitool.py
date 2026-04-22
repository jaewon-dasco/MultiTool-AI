# -*- coding: utf-8 -*-
"""
MultiTool UI 탐색 스크립트
- MultiTool 실행 후 UI 트리 구조 출력
- 메뉴 항목 및 컨트롤 목록 파악
"""
import subprocess
import time
from pathlib import Path

MULTITOOL_EXE = r"C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe"
MTPROJECT_PATH = Path(r"C:\Users\JONE\Desktop\EPEC\CoDeSysProject\DasDemoProject\DasDemoProject.mtproject")

try:
    from pywinauto import Application, Desktop
    from pywinauto.keyboard import send_keys
except ImportError:
    print("pywinauto 없음. py -m pip install pywinauto")
    raise


def start_multitool():
    print("MultiTool 실행 중...")
    proc = subprocess.Popen([MULTITOOL_EXE, str(MTPROJECT_PATH)])
    time.sleep(4)
    return proc


def connect_to_multitool():
    app = Application(backend='win32').connect(path=MULTITOOL_EXE, timeout=10)
    return app


def print_ui_tree(app):
    win = app.top_window()
    print(f"\n=== 메인 윈도우 ===")
    print(f"Title : {win.window_text()}")
    print(f"Class : {win.class_name()}")
    print(f"Rect  : {win.rectangle()}")

    print("\n=== 자식 컨트롤 (depth=2) ===")
    try:
        win.print_control_identifiers(depth=2)
    except Exception as e:
        print(f"  오류: {e}")


def list_menus(app):
    win = app.top_window()
    print("\n=== 메뉴 항목 ===")
    try:
        menu = win.menu()
        if menu:
            for i in range(menu.item_count()):
                item = menu.item(i)
                print(f"  [{i}] {item.text()}")
    except Exception as e:
        print(f"  메뉴 접근 오류: {e}")


def list_all_windows():
    print("\n=== 열린 윈도우 목록 ===")
    desktop = Desktop(backend='win32')
    for win in desktop.windows():
        try:
            title = win.window_text()
            cls = win.class_name()
            if title:
                print(f"  '{title}' [{cls}]")
        except Exception:
            pass


if __name__ == '__main__':
    list_all_windows()

    start_multitool()

    try:
        app = connect_to_multitool()
        print_ui_tree(app)
        list_menus(app)
    except Exception as e:
        print(f"\n연결 실패: {e}")
        list_all_windows()
