# -*- coding: utf-8 -*-
"""
MultiTool .exp 생성 패턴 테스트
1. 현재 .exp 백업
2. .mtproject XML에 테스트 변경 적용
3. MultiTool 재실행 → Ctrl+Alt+E → .exp 생성
4. before/after diff 출력
"""
import subprocess
import time
import shutil
import difflib
from pathlib import Path

MULTITOOL_EXE = r"C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe"
MTPROJECT_PATH = Path(r"C:\Users\JONE\Desktop\EPEC\CoDeSysProject\DasDemoProject\DasDemoProject.mtproject")
LOCKFILE = MTPROJECT_PATH.parent / "~$projlock.mtproject"
EXP_PATH = Path(r"C:\Users\JONE\Desktop\EPEC\CoDeSysProject\DasDemoProject\CU_3606_21\CU_3606_21.exp")
EXP_BACKUP = EXP_PATH.parent / "CU_3606_21_before_test.exp"

try:
    import win32api
    import win32con
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    from pywinauto import Application
    from pywinauto.keyboard import send_keys
    HAS_PYWINAUTO = True
except ImportError:
    HAS_PYWINAUTO = False


# ── MultiTool 제어 ─────────────────────────────────────────────────────────────

def close_multitool():
    result = subprocess.run(['taskkill', '/F', '/IM', 'MultiTool.exe'], capture_output=True)
    if result.returncode == 0:
        print("[1] MultiTool 종료됨 — 잠금 파일 해제 대기...")
        for _ in range(20):
            if not LOCKFILE.exists():
                break
            time.sleep(0.5)
    else:
        print("[1] MultiTool 미실행")


def open_multitool(wait=5):
    print(f"[3] MultiTool 실행 중... ({wait}초 대기)")
    subprocess.Popen([MULTITOOL_EXE, str(MTPROJECT_PATH)])
    time.sleep(wait)


def find_multitool_hwnd():
    """MultiTool 메인 윈도우 핸들 검색"""
    hwnd = None
    def callback(h, _):
        nonlocal hwnd
        title = win32gui.GetWindowText(h)
        if 'MultiTool' in title and win32gui.IsWindowVisible(h):
            hwnd = h
    win32gui.EnumWindows(callback, None)
    return hwnd


def send_export_shortcut():
    """Ctrl+Alt+E 전송으로 .exp 생성 트리거"""
    if HAS_WIN32:
        hwnd = find_multitool_hwnd()
        if hwnd:
            print(f"[4] MultiTool 윈도우 발견 (hwnd={hwnd:#010x})")
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.5)
        else:
            print("[4] MultiTool 윈도우 못 찾음 — 활성 창에 키 전송")

    if HAS_PYWINAUTO:
        try:
            app = Application(backend='win32').connect(title_re='.*MultiTool.*', timeout=5)
            win = app.top_window()
            win.set_focus()
            time.sleep(0.3)
            send_keys('^%e')  # Ctrl+Alt+E
            print("[4] Ctrl+Alt+E 전송 완료")
        except Exception as e:
            print(f"[4] pywinauto 키 전송 실패: {e}")
            _send_keys_fallback()
    else:
        _send_keys_fallback()


def _send_keys_fallback():
    """win32api로 직접 키 전송"""
    if not HAS_WIN32:
        print("[4] win32api 없음")
        return
    hwnd = find_multitool_hwnd()
    if not hwnd:
        print("[4] 윈도우 없음")
        return
    VK_CONTROL, VK_MENU, VK_E = 0x11, 0x12, 0x45
    win32api.keybd_event(VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(VK_MENU, 0, 0, 0)
    win32api.keybd_event(VK_E, 0, 0, 0)
    time.sleep(0.1)
    win32api.keybd_event(VK_E, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
    print("[4] Ctrl+Alt+E 전송 완료 (fallback)")


# ── XML 변경 (테스트) ──────────────────────────────────────────────────────────

def apply_test_change():
    """테스트용 변경: CAN1 HeartbeatInterval 200 → 300"""
    from xml.etree import ElementTree as ET
    tree = ET.parse(MTPROJECT_PATH)
    root = tree.getroot()
    changed = False
    for el in root.findall('.//HeartbeatInterval'):
        old = el.text
        el.text = '300'
        print(f"[2] HeartbeatInterval: {old} → 300")
        changed = True
        break
    if changed:
        ET.indent(tree, space='  ')
        tree.write(MTPROJECT_PATH, encoding='utf-8', xml_declaration=True)
    return changed


def revert_test_change():
    """테스트 변경 되돌리기: 300 → 200"""
    from xml.etree import ElementTree as ET
    tree = ET.parse(MTPROJECT_PATH)
    root = tree.getroot()
    for el in root.findall('.//HeartbeatInterval'):
        el.text = '200'
        break
    ET.indent(tree, space='  ')
    tree.write(MTPROJECT_PATH, encoding='utf-8', xml_declaration=True)
    print("[R] HeartbeatInterval 원복: 300 → 200")


# ── diff 비교 ─────────────────────────────────────────────────────────────────

def show_diff(before_path, after_path, context=5):
    before = before_path.read_text(encoding='utf-8', errors='replace').splitlines()
    after = after_path.read_text(encoding='utf-8', errors='replace').splitlines()
    diff = list(difflib.unified_diff(before, after,
                                     fromfile='before.exp', tofile='after.exp',
                                     lineterm='', n=context))
    if diff:
        print(f"\n=== .exp 변경 ({len(diff)}줄) ===")
        for line in diff[:200]:  # 최대 200줄
            print(line)
    else:
        print("\n=== .exp 변경 없음 ===")


# ── 메인 ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # 0. 현재 .exp 백업
    if EXP_PATH.exists():
        shutil.copy2(EXP_PATH, EXP_BACKUP)
        print(f"[0] .exp 백업: {EXP_BACKUP.name}")

    # 1. MultiTool 종료
    close_multitool()

    # 2. XML 변경
    if not apply_test_change():
        print("[2] 변경 실패 — 종료")
        exit(1)

    # 3. MultiTool 재실행
    open_multitool(wait=6)

    # 4. Ctrl+Alt+E로 .exp 생성
    send_export_shortcut()
    print("[5] .exp 생성 대기 (5초)...")
    time.sleep(5)

    # 5. diff 확인
    if EXP_BACKUP.exists() and EXP_PATH.exists():
        show_diff(EXP_BACKUP, EXP_PATH)
    else:
        print("[5] .exp 파일 없음 — 생성 실패")

    # 6. 원복 여부 확인
    revert = input("\n변경사항을 원복할까요? (y/n): ").strip().lower()
    if revert == 'y':
        close_multitool()
        revert_test_change()
        open_multitool(wait=4)
        print("원복 완료.")
