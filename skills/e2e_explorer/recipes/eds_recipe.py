"""EDS 파일 등록 — Add Slave Device → Generic → 파일 다이얼로그.

probe_add_slave_generic 검증 (2026-05-20):
- Network Editor toolbar 2nd DropDownPart (361, 85) click
- 메뉴 등장 → 'Generic' Text (388, 353) click
- 파일 다이얼로그 등장: 'Select file for added generic unit' (win32 #32770)
- EDS 경로 send_keys + Enter → 디바이스 추가

지원 형식: EDS, DCF, XDD, XDC
"""
import time
from pathlib import Path
from pywinauto import mouse, Desktop
from pywinauto.keyboard import send_keys
from . import common


DEFAULT_EDS_PATH = r"C:\Program Files (x86)\Epec\MultiTool Creator 8.4\Resources\Config\SlaveDeviceTemplates\Eds\GC44_Epec.eds"


def open_add_slave_dropdown(win):
    """Network Editor toolbar 2nd DropDownPart 클릭."""
    drops = []
    for b in win.descendants(control_type="Button"):
        try:
            n = b.window_text() or ""
            r = b.rectangle()
            if n == "DropDownPart" and r.top < 150:
                drops.append((b, r))
        except Exception: pass
    drops.sort(key=lambda x: x[1].left)
    if len(drops) < 2: return False
    drops[1][0].click_input()
    time.sleep(1.5)
    return True


def click_generic_menuitem(win):
    """드롭다운 메뉴에서 'Generic' Text 클릭."""
    for t in win.descendants(control_type="Text"):
        try:
            if t.window_text() == "Generic":
                t.click_input()
                time.sleep(2.5)
                return True
        except Exception: pass
    return False


def wait_file_dialog(timeout: float = 5):
    """파일 다이얼로그 'Select file for added generic unit' 대기."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        for w in Desktop(backend="win32").windows():
            try:
                t = w.window_text() or ""
                if "Select file" in t and "generic" in t.lower():
                    return w
            except Exception: pass
        time.sleep(0.5)
    return None


def add_slave_from_eds(win, eds_path: str = DEFAULT_EDS_PATH) -> dict:
    """전체 흐름: Add Slave Device → Generic → 파일 선택 → 디바이스 등록."""
    result = {"ok": False, "kind": "eds_add_slave", "action": None,
              "eds_path": eds_path}

    if not Path(eds_path).exists():
        result["action"] = f"eds_file_not_found {eds_path}"; return result

    # 1. Open dropdown
    if not open_add_slave_dropdown(win):
        result["action"] = "add_slave_dropdown_failed"; return result

    # 2. Click Generic
    if not click_generic_menuitem(win):
        result["action"] = "generic_menuitem_not_found"
        send_keys("{ESC}"); return result

    # 3. Wait file dialog
    dlg = wait_file_dialog(timeout=5)
    if dlg is None:
        result["action"] = "file_dialog_not_opened"
        send_keys("{ESC}"); return result

    # 4. Type path + Enter
    send_keys(eds_path.replace(" ", "{SPACE}"), pause=0.02)
    time.sleep(0.5)
    send_keys("{ENTER}")
    time.sleep(3.0)

    result["ok"] = True
    result["action"] = f"eds.add_slave '{Path(eds_path).name}'"
    return result
