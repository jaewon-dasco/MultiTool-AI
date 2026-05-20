"""PDO 탭 toolbar 액션 — Transmit/Receive PDOs 섹션별 Add/Remove.

사용자 검증 (2026-05-20):
- PDO toolbar 버튼은 라벨이 노출됨: "Add Transmit PDO" / "Remove Transmit PDO"
  / "Add Receive PDO" / "Remove Receive PDO"
- 이름 매칭이 1차, 위치 기반은 fallback
"""
import time
from . import common


SECTIONS = {"Tx": "Transmit PDOs", "Rx": "Receive PDOs"}
DIRECTION_FULL = {"Tx": "Transmit", "Rx": "Receive"}


def find_pdo_toolbar_button(win, direction: str, action: str):
    """direction: 'Tx' or 'Rx'. action: 'Add' or 'Remove'.
    반환: (button, rect) 또는 (None, None).
    1차: 버튼 name == "{action} {Transmit|Receive} PDO" 매칭
    2차: 섹션 헤더 우측 좌→우 인덱스(0=Add, 1=Remove) fallback"""
    full_dir = DIRECTION_FULL.get(direction)
    if not full_dir: return None, None
    target_name = f"{action} {full_dir} PDO"

    for b in win.descendants(control_type="Button"):
        try:
            if (b.window_text() or "").strip() == target_name:
                return b, b.rectangle()
        except Exception: pass

    # Fallback: 좌표/인덱스 기반
    header_text = SECTIONS.get(direction)
    if not header_text: return None, None
    header_rect = None
    for t in win.descendants(control_type="Text"):
        try:
            if t.window_text() == header_text:
                header_rect = t.rectangle(); break
        except Exception: pass
    if header_rect is None: return None, None

    y_mid = (header_rect.top + header_rect.bottom) // 2
    btns = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            if abs((r.top + r.bottom)//2 - y_mid) < 25 and r.left > header_rect.right and r.left < header_rect.right + 250 and r.width() < 50:
                btns.append((b, r))
        except Exception: pass
    btns.sort(key=lambda x: x[1].left)
    idx = 0 if action == "Add" else 1
    if idx >= len(btns): return None, None
    return btns[idx]


def find_first_pdo_row(win, direction: str):
    """Tx/Rx 섹션 첫 데이터 행 찾기. 헤더 y 직후의 DataItem 또는 COB-ID 값이 있는 첫 행."""
    header_text = SECTIONS.get(direction)
    if not header_text: return None
    header_rect = None
    for t in win.descendants(control_type="Text"):
        try:
            if t.window_text() == header_text:
                header_rect = t.rectangle(); break
        except Exception: pass
    if header_rect is None: return None
    # Header bottom 이후 ~50px 내의 DataItem
    for d in win.descendants(control_type="DataItem"):
        try:
            r = d.rectangle()
            if header_rect.bottom < r.top < header_rect.bottom + 400 and r.height() > 5:
                return d, r
        except Exception: pass
    return None


def pdo_remove_or_select_and_remove(win, direction: str, value: str = None) -> dict:
    """PDO Remove — 먼저 첫 행 클릭으로 선택 → Remove 버튼 클릭.

    Remove 버튼은 행이 선택돼야 활성화됨 (사용자 검증 2026-05-19).
    """
    result = {"ok": False, "kind": "pdo_toolbar", "action": None,
              "direction": direction, "remove_action": "Remove"}

    # 1. 첫 행 선택 (없으면 Add 선행)
    row_info = find_first_pdo_row(win, direction)
    if row_info is None:
        add_res = pdo_add(win, direction)
        if not add_res.get("ok"):
            result["action"] = f"{direction}_no_data_row_add_failed"; return result
        # Add 후 렌더링 지연 대응 — 최대 10초까지 0.5s 폴링
        for _ in range(20):
            time.sleep(0.5)
            row_info = find_first_pdo_row(win, direction)
            if row_info is not None: break
        if row_info is None:
            result["action"] = f"{direction}_add_succeeded_but_row_missing"; return result
    row, rrect = row_info
    try:
        row.click_input()
        time.sleep(0.5)
    except Exception as e:
        result["action"] = f"row_click_exception: {e}"; return result

    # 2. Remove 버튼 클릭
    btn, rect = find_pdo_toolbar_button(win, direction, "Remove")
    if btn is None:
        result["action"] = f"{direction}_remove_button_not_found"; return result
    try:
        btn.click_input()
        time.sleep(0.8)
        result["ok"] = True
        result["action"] = f"pdo.{direction.lower()}.select_first_row+remove"
        return result
    except Exception as e:
        result["action"] = f"remove_exception: {e}"
        return result


def pdo_add(win, direction: str) -> dict:
    result = {"ok": False, "kind": "pdo_toolbar", "action": None, "direction": direction}
    btn, rect = find_pdo_toolbar_button(win, direction, "Add")
    if btn is None:
        result["action"] = f"{direction}_add_button_not_found"; return result
    try:
        btn.click_input()
        time.sleep(0.8)
        result["ok"] = True
        result["action"] = f"pdo.{direction.lower()}.add"
        return result
    except Exception as e:
        result["action"] = f"exception: {e}"
        return result
