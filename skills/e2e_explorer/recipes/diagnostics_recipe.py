"""Diagnostics 탭 alarm limit 편집 — UIA 기반 핸들러.

구조 (probe_diagnostics_uia 검증):
  - CheckBox "Xxx alarm limits" / "Xxx alarm limit" (행 식별)
  - 같은 행 y범위 내 Edit 2개: 왼쪽=Min(x=499-681), 오른쪽=Max(x=700-882)
  - Min/Max 누락 행도 존재 (단순 toggle만, Edit 없음)
"""
import time
from . import common


def find_alarm_row(win, label_keyword: str):
    """CheckBox 이름에 label_keyword가 포함된 행 찾기. (CheckBox, rect) 반환 or (None,None)."""
    kw = label_keyword.lower()
    for cb in win.descendants(control_type="CheckBox"):
        try:
            n = (cb.window_text() or "")
            if kw in n.lower():
                return cb, cb.rectangle()
        except Exception: pass
    return None, None


def find_minmax_edits(win, row_rect, min_x_min=400, min_x_max=700, max_x_min=700, max_x_max=900):
    """행 y범위 내 Edit 컨트롤 2개 (Min, Max). y_mid가 row 범위 안에 있는 Edit."""
    y_mid = (row_rect.top + row_rect.bottom) // 2
    min_edit = None; max_edit = None
    for e in win.descendants(control_type="Edit"):
        try:
            r = e.rectangle()
            r_y = (r.top + r.bottom) // 2
            if abs(r_y - y_mid) > 20: continue
            if min_x_min <= r.left <= min_x_max:
                if min_edit is None or r.left < min_edit.rectangle().left:
                    min_edit = e
            elif max_x_min <= r.left <= max_x_max:
                if max_edit is None or r.left < max_edit.rectangle().left:
                    max_edit = e
        except Exception: pass
    return min_edit, max_edit


def set_alarm_limit(win, label_keyword: str, which: str, value: str) -> dict:
    """label_keyword 매칭 행의 Min/Max Edit 값 변경.

    label_keyword: 'Temperature', 'Supply voltage', 'REF 5 V', 'Cycle time', 'REF internal 2.5 V'
    which: 'Min' or 'Max'
    """
    from pywinauto.keyboard import send_keys
    result = {"ok": False, "kind": "diagnostics_minmax", "action": None,
              "label": label_keyword, "which": which, "value": value}

    cb, row_rect = find_alarm_row(win, label_keyword)
    if cb is None:
        result["action"] = f"alarm_row_not_found '{label_keyword}'"; return result

    min_edit, max_edit = find_minmax_edits(win, row_rect)
    target = min_edit if which.lower().startswith("min") else max_edit
    if target is None:
        result["action"] = f"{which} edit not_found '{label_keyword}'"; return result

    try:
        target.click_input()
        time.sleep(0.3)
        send_keys("^a"); time.sleep(0.1)
        send_keys("{DELETE}"); time.sleep(0.1)
        send_keys(value, with_spaces=True); time.sleep(0.2)
        send_keys("{TAB}"); time.sleep(0.4)
        result["ok"] = True
        result["action"] = f"diag.{which.lower()}.set '{value}' @ '{label_keyword}'"
        return result
    except Exception as e:
        result["action"] = f"exception: {e}"
        return result
