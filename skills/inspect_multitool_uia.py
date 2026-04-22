# -*- coding: utf-8 -*-
"""MultiTool UIA 백엔드 UI 트리 탐색"""
import time
from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys
import win32gui


def find_multitool_hwnd():
    result = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if 'MultiTool' in t and win32gui.IsWindowVisible(h):
            result.append((h, t))
    win32gui.EnumWindows(cb, None)
    return result


print("=== MultiTool 윈도우 목록 ===")
hwnds = find_multitool_hwnd()
for h, t in hwnds:
    print(f"  {h:#010x}  '{t}'")

# UIA 백엔드로 연결
print("\n=== UIA 백엔드 연결 시도 ===")
try:
    app_uia = Application(backend='uia').connect(title_re='.*MultiTool.*', timeout=5)
    win = app_uia.top_window()
    print(f"연결 성공: '{win.window_text()}'")
    print(f"Rect: {win.rectangle()}")

    print("\n=== UIA 컨트롤 트리 (depth=4) ===")
    win.print_control_identifiers(depth=4)

except Exception as e:
    print(f"UIA 연결 실패: {e}")

# win32 백엔드도 시도
print("\n=== win32 백엔드 연결 시도 ===")
try:
    app32 = Application(backend='win32').connect(title_re='.*MultiTool.*', timeout=5)
    win32 = app32.top_window()
    print(f"연결 성공: '{win32.window_text()}'")
    print("\n=== win32 컨트롤 트리 (depth=3) ===")
    win32.print_control_identifiers(depth=3)
except Exception as e:
    print(f"win32 연결 실패: {e}")
