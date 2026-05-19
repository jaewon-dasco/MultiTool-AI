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


def set_pin_variable_name(win, pin_id: str, new_name: str,
                           connector: str = CONNECTOR_DEFAULT) -> dict:
    """핀 셀 더블클릭 → 우측 패널 Edit에서 Variable Name 변경.

    동작 (2026-05-19 probe_io_variable_name 검증):
    - 핀 행의 Variable Name 컬럼 셀(x=284-418) 더블클릭
    - 우측 패널(x=1374+, y=125 부근)에 Edit 컨트롤 등장 (현재 값 채워져 있음)
    - Edit click_input → Ctrl+A → DELETE → new_name → ENTER
    """
    from pywinauto import mouse
    from pywinauto.keyboard import send_keys

    result = {"ok": False, "kind": "io_variable_name", "action": None,
              "pin": pin_id, "value": new_name}

    if not expand_connector(win, connector):
        result["action"] = "expand_connector_failed"; return result
    pin_rect = find_pin_row_rect(win, pin_id)
    if pin_rect is None:
        result["action"] = f"pin_row_not_found pin={pin_id}"; return result

    # Variable Name 컬럼 셀 중앙 (probe 기반: x 284-418)
    vn_cx = (284 + 418) // 2
    vn_cy = (pin_rect.top + pin_rect.bottom) // 2
    mouse.double_click(coords=(vn_cx, vn_cy))
    time.sleep(0.8)

    # 우측 패널 Edit 찾기 — y는 핀 행과 무관하게 우측 패널 y=125 부근, name=현재 변수명
    target_edit = None
    for e in win.descendants(control_type="Edit"):
        try:
            r = e.rectangle()
            if r.left >= 1300 and r.top < 200 and r.width() > 200:
                # 가장 위의 Edit (Variable Name 위치 가정)
                if target_edit is None or e.rectangle().top < target_edit.rectangle().top:
                    target_edit = e
        except Exception: pass

    if target_edit is None:
        result["action"] = "variable_name_edit_not_found"; return result

    try:
        target_edit.click_input()
        time.sleep(0.3)
        send_keys("^a"); time.sleep(0.1)
        send_keys("{DELETE}"); time.sleep(0.1)
        send_keys(new_name, with_spaces=True); time.sleep(0.2)
        send_keys("{ENTER}"); time.sleep(0.4)
        result["ok"] = True
        result["action"] = f"io_var_name.set '{new_name}' @ pin={pin_id}"
        return result
    except Exception as e:
        result["action"] = f"exception: {e}"
        return result


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
