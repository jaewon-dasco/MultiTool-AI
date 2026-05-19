"""I/O 패널 핀 모드 변경 — UIA 기반 (OCR 우회).

MultiTool I/O 패널은 WPF RadTreeListView 가상화 + 비텍스트 셀로 OCR이 무력함.
대신 UIA 트리에서 DataItem name(핀 번호)으로 행을 찾고, Modes 컬럼의 Button을
click_input()으로 직접 클릭.

핵심 규칙:
  - mouse.click(coords) 는 WPF DataGrid 셀에 동작 안 함
  - 반드시 UIA element.click_input() 사용
  - 커넥터 chevron(좌측 ~22px Button)을 먼저 펼쳐야 핀 행들이 노출

사용:
  set_pin_mode(win, pin_id="1.2", mode_short="DI")
"""
import time
from . import common

CONNECTOR_DEFAULT = "1"


def expand_connector(win, conn_name: str = CONNECTOR_DEFAULT) -> bool:
    """커넥터 행 chevron을 click_input()으로 펼침. 이미 펼쳐져있어도 무해 (한 번 더 토글되지 않도록 자식 존재 확인)."""
    # 이미 자식 핀이 노출되어 있는지 확인 (DataItem name="<conn>.X" 다수)
    children = 0
    for d in win.descendants(control_type="DataItem"):
        try:
            n = d.window_text()
            if n and n.startswith(conn_name + "."):
                children += 1
                if children >= 3: break
        except Exception: pass
    if children >= 3:
        return True

    # chevron 탐색: 커넥터 행 y범위 내 x≤230 좁은 Button
    conn_rect = None
    for d in win.descendants(control_type="DataItem"):
        try:
            if d.window_text() == conn_name and d.rectangle().height() > 5:
                conn_rect = d.rectangle(); break
        except Exception: pass
    if conn_rect is None:
        return False
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            if (r.left >= conn_rect.left - 5 and r.right <= conn_rect.left + 30
                and r.top >= conn_rect.top and r.bottom <= conn_rect.bottom
                and r.width() <= 30 and r.height() <= 30):
                b.click_input()
                time.sleep(1.0)
                return True
        except Exception: pass
    return False


def find_pin_row_rect(win, pin_id: str):
    """핀 번호(예: '1.2') DataItem의 rectangle 반환."""
    for d in win.descendants(control_type="DataItem"):
        try:
            if d.window_text() == pin_id and d.rectangle().height() > 5:
                return d.rectangle()
        except Exception: pass
    return None


def list_mode_buttons(win, pin_rect, modes_col_x_min: int = 410) -> list:
    """핀 행 내 Modes 컬럼의 Button 목록 — (element, name, rect) 튜플."""
    out = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            if (r.left >= modes_col_x_min
                and r.top >= pin_rect.top - 2 and r.bottom <= pin_rect.bottom + 2
                and r.width() >= 15 and r.width() <= 200):
                n = b.window_text() or ""
                if n: out.append((b, n, r))
        except Exception: pass
    out.sort(key=lambda x: x[2].left)
    return out


def set_pin_mode(win, pin_id: str, mode_short: str, connector: str = CONNECTOR_DEFAULT) -> dict:
    """핀 모드 버튼 클릭. mode_short: 버튼 이름 (예: 'DI','DO','AI','AO','GND')."""
    result = {"ok": False, "kind": "io_mode_button", "action": None, "pin": pin_id, "mode": mode_short}

    if not expand_connector(win, connector):
        result["action"] = f"expand_connector_failed conn={connector}"; return result

    pin_rect = find_pin_row_rect(win, pin_id)
    if pin_rect is None:
        result["action"] = f"pin_row_not_found pin={pin_id}"; return result

    buttons = list_mode_buttons(win, pin_rect)
    if not buttons:
        result["action"] = f"no_mode_buttons pin={pin_id}"; return result

    matches = [(b, n, r) for b, n, r in buttons if n.strip().lower() == mode_short.strip().lower()]
    if not matches:
        avail = [n for _, n, _ in buttons]
        result["action"] = f"mode '{mode_short}' not_available pin={pin_id} have={avail}"
        result["available_modes"] = avail
        return result

    btn, n, _ = matches[0]
    btn.click_input()
    time.sleep(0.6)
    result["ok"] = True
    result["action"] = f"io_mode.click '{n}' @ pin={pin_id}"
    return result
