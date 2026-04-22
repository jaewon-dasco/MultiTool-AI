# -*- coding: utf-8 -*-
"""MultiTool 내부 UIA 트리 심층 탐색 + 윈도우 위치 교정"""
import time
import win32gui
import win32con
from pywinauto import Application
from pywinauto.keyboard import send_keys


def move_window_to_screen(hwnd, x=100, y=50, w=1400, h=900):
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.MoveWindow(hwnd, x, y, w, h, True)
    time.sleep(0.3)
    print(f"윈도우 이동: ({x},{y}) {w}x{h}")


def find_multitool_hwnd():
    result = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if 'MultiTool' in t and win32gui.IsWindowVisible(h):
            result.append((h, t))
    win32gui.EnumWindows(cb, None)
    return result


hwnds = find_multitool_hwnd()
if not hwnds:
    print("MultiTool 윈도우 없음")
    exit(1)

hwnd, title = hwnds[0]
print(f"발견: {hwnd:#010x} '{title}'")
rect = win32gui.GetWindowRect(hwnd)
print(f"현재 위치: {rect}")

# 화면 밖이면 이동
if rect[0] < 0 or rect[1] < 0:
    move_window_to_screen(hwnd)

# UIA 연결
app = Application(backend='uia').connect(handle=hwnd, timeout=5)
win = app.top_window()
rect = win.rectangle()
print(f"이동 후 위치: {rect}")

# Rad Split Container 하위 탐색
print("\n=== Rad Split Container 하위 (depth=6) ===")
try:
    container = win.child_window(title="Rad Split Container", control_type="Custom")
    container.print_control_identifiers(depth=6)
except Exception as e:
    print(f"오류: {e}")

# 전체 트리에서 TreeView/TreeItem 찾기
print("\n=== TreeItem 목록 ===")
try:
    items = win.descendants(control_type="TreeItem")
    for item in items[:30]:
        try:
            print(f"  '{item.window_text()}' auto_id='{item.automation_id()}'")
        except Exception:
            pass
except Exception as e:
    print(f"오류: {e}")

# 전체 트리에서 Pane/Custom 컨트롤 목록
print("\n=== Custom 컨트롤 목록 ===")
try:
    customs = win.descendants(control_type="Custom")
    for c in customs[:20]:
        try:
            txt = c.window_text()
            aid = c.automation_id()
            if txt or aid:
                print(f"  '{txt}' auto_id='{aid}' rect={c.rectangle()}")
        except Exception:
            pass
except Exception as e:
    print(f"오류: {e}")

# TabItem 목록 (좌측 패널 탭)
print("\n=== TabItem 목록 ===")
try:
    tabs = win.descendants(control_type="TabItem")
    for t in tabs[:20]:
        try:
            print(f"  '{t.window_text()}' auto_id='{t.automation_id()}'")
        except Exception:
            pass
except Exception as e:
    print(f"오류: {e}")
