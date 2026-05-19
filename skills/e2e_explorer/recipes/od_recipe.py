"""OD (Object Dictionary) 탭 toolbar 액션 — 행 선택 상태별 분기.

probe_od_after_rowselect 검증 (2026-05-20):
- toolbar 6 RadButton (rect 265~515, y=121~157), name·auto_id 모두 비어있음
- 행 선택 여부에 따라 같은 idx의 버튼 기능이 변경:
  - idx 0: 선택 전=Add Index / 선택 후=Remove
  - idx 1: 선택 전=Add Pre-defined Index / 선택 후=Add Sub-Index
  - idx 2~5: Show Hidden / Store/Restore / Import / Export (고정)
"""
import time
from . import common


TOOLBAR_X_MIN = 260
TOOLBAR_X_MAX = 700
TOOLBAR_Y_MIN = 105
TOOLBAR_Y_MAX = 165


def find_od_toolbar_buttons(win):
    """OD toolbar 6개 Button을 좌→우 순으로 반환."""
    btns = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            if (TOOLBAR_X_MIN < r.left < TOOLBAR_X_MAX
                and TOOLBAR_Y_MIN < r.top < TOOLBAR_Y_MAX
                and 10 < r.width() < 80):
                btns.append((b, r))
        except Exception: pass
    btns.sort(key=lambda x: x[1].left)
    return btns


def find_first_od_row(win):
    """OD 본문 영역(y>180)의 첫 DataItem."""
    for d in win.descendants(control_type="DataItem"):
        try:
            r = d.rectangle()
            if r.top > 180 and r.height() > 5 and r.width() > 100:
                return d
        except Exception: pass
    return None


def click_od_toolbar_idx(win, idx: int, after_row_select: bool = False,
                          target_row=None) -> dict:
    """OD toolbar의 idx 버튼 클릭. after_row_select=True면 첫 행을 먼저 선택."""
    result = {"ok": False, "kind": "od_toolbar", "action": None, "idx": idx,
              "after_row_select": after_row_select}

    if after_row_select:
        row = target_row or find_first_od_row(win)
        if row is None:
            result["action"] = "no_data_row"; return result
        try:
            row.click_input(); time.sleep(0.8)
        except Exception as e:
            result["action"] = f"row_click_exception: {e}"; return result

    btns = find_od_toolbar_buttons(win)
    if idx >= len(btns):
        result["action"] = f"button_idx_{idx}_out_of_range len={len(btns)}"; return result

    btn = btns[idx][0]
    try:
        btn.click_input(); time.sleep(0.8)
        result["ok"] = True
        result["action"] = f"od.toolbar[{idx}].click (after_row_select={after_row_select})"
        return result
    except Exception as e:
        result["action"] = f"exception: {e}"
        return result


# 시드명 → (idx, after_row_select) 매핑
OD_ACTION_MAP = {
    "add_index":         (0, False),
    "add_predefined":    (1, False),
    "remove":            (0, True),    # 행 선택 후 idx 0
    "add_subindex":      (1, True),    # Index 행 선택 후 idx 1
    "show_hidden":       (2, False),
    "store_restore":     (3, False),
    "import":            (4, False),
    "export":            (5, False),
}


def execute_od_action(win, action_name: str) -> dict:
    """시드 action_name(예: 'add_index')으로 자동 분기."""
    if action_name not in OD_ACTION_MAP:
        return {"ok": False, "kind": "od_toolbar",
                "action": f"unknown_action {action_name}"}
    idx, after_row = OD_ACTION_MAP[action_name]
    r = click_od_toolbar_idx(win, idx, after_row_select=after_row)
    r["action_name"] = action_name
    return r
