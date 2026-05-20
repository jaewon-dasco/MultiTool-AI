"""Network Editor 'Add Device' / 'Add Slave Device' — 4-column ListMenu 자동화.

probe_add_device_dropdown 검증 (2026-05-19~20):
- Network Editor toolbar에 DropDownPart 2개 (top<150):
  - drops[0] = Add Device
  - drops[1] = Add Slave Device (eds_recipe와 공유)
- DropDownPart 클릭 시 Window rect=[265,121,697,411] 등장
- 4 컬럼: Product family / Device / Functional Version / CODESYS Version
- 각 컬럼 List 안 ListItem name은 LINQ Grouping 객체 → 자식 Text의 window_text()로 식별

지원 family: 2000/3000/4000/5000/6000-X/S-E series
"""
import time
from pywinauto.keyboard import send_keys
from . import common


# 모델 prefix → family 자동 매핑 (CU_3606_xx → 3000 series 등)
MODEL_TO_FAMILY = {
    "2": "2000 series",
    "3": "3000 series",
    "4": "4000 series",
    "5": "5000 series",
    "6": "6000/X series",
}


def infer_family(model: str) -> str:
    """CU_3606_21 → '3000 series' (모델 prefix 첫 숫자 기반)."""
    digits = "".join(c for c in model if c.isdigit())
    if digits:
        return MODEL_TO_FAMILY.get(digits[0], "")
    return ""


def find_add_device_dropdowns(win):
    """toolbar top<150 DropDownPart 2개 (Add Device, Add Slave Device)."""
    drops = []
    for b in win.descendants(control_type="Button"):
        try:
            n = b.window_text() or ""
            r = b.rectangle()
            if n == "DropDownPart" and r.top < 150:
                drops.append((b, r))
        except Exception: pass
    drops.sort(key=lambda x: x[1].left)
    return drops


def select_column_item(win, column_x_range, target_text: str, timeout: float = 3.0):
    """4-column ListMenu에서 특정 컬럼(x 범위)의 ListItem을 target_text로 찾아 클릭.

    각 ListItem의 표시 텍스트는 자식 Text 컨트롤의 window_text(). LINQ Grouping name은 무시.
    """
    x_min, x_max = column_x_range
    t0 = time.time()
    while time.time() - t0 < timeout:
        for t in win.descendants(control_type="Text"):
            try:
                if (t.window_text() or "").strip() == target_text:
                    tr = t.rectangle()
                    if x_min <= tr.left <= x_max and tr.top > 140:
                        t.click_input()
                        time.sleep(0.6)
                        return True
            except Exception: pass
        time.sleep(0.3)
    return False


def _select_column_item_contains(win, column_x_range, substring: str, timeout: float = 2.0):
    """컬럼 텍스트가 substring을 포함하는 항목 클릭. 모델명 변형 대응(공백/하이픈)."""
    x_min, x_max = column_x_range
    # 모델 비교 시 영숫자만 비교
    sub_norm = "".join(c for c in substring if c.isalnum()).upper()
    t0 = time.time()
    while time.time() - t0 < timeout:
        for t in win.descendants(control_type="Text"):
            try:
                txt = (t.window_text() or "").strip()
                txt_norm = "".join(c for c in txt if c.isalnum()).upper()
                if sub_norm and sub_norm in txt_norm:
                    tr = t.rectangle()
                    if x_min <= tr.left <= x_max and tr.top > 140:
                        t.click_input(); time.sleep(0.6); return True
            except Exception: pass
        time.sleep(0.3)
    return False


def _select_column_item_startswith(win, column_x_range, prefix: str, timeout: float = 2.0):
    """컬럼 텍스트가 prefix로 시작하는 항목 클릭 (정확 일치 fallback)."""
    x_min, x_max = column_x_range
    t0 = time.time()
    while time.time() - t0 < timeout:
        for t in win.descendants(control_type="Text"):
            try:
                txt = (t.window_text() or "").strip()
                if txt.startswith(prefix):
                    tr = t.rectangle()
                    if x_min <= tr.left <= x_max and tr.top > 140:
                        t.click_input(); time.sleep(0.6); return True
            except Exception: pass
        time.sleep(0.3)
    return False


def select_first_in_column(win, column_x_range, timeout: float = 2.0):
    """컬럼의 첫 ListItem 클릭 (기본값 선택 용)."""
    x_min, x_max = column_x_range
    t0 = time.time()
    while time.time() - t0 < timeout:
        items = []
        for li in win.descendants(control_type="ListItem"):
            try:
                r = li.rectangle()
                if x_min <= r.left <= x_max and r.top > 140:
                    items.append((li, r))
            except Exception: pass
        if items:
            items.sort(key=lambda x: x[1].top)
            items[0][0].click_input()
            time.sleep(0.6)
            return True
        time.sleep(0.3)
    return False


COLUMN_X = {
    "family":  (265, 427),
    "device":  (428, 475),
    "func":    (476, 589),
    "cds":     (590, 696),
}


def add_device_via_dropdown(win, model: str, cds: str = "2.3",
                            family: str = None, slave: bool = False) -> dict:
    """4-column dropdown을 거쳐 디바이스 추가.

    model:   'CU_3606_21' 등 (column 2 매칭)
    cds:     '2.3' 또는 '3.5' (column 4 매칭)
    family:  명시 안 하면 model에서 추론
    slave:   True면 Add Slave Device dropdown 사용
    """
    result = {"ok": False, "kind": "toolbar_action_with_dialog",
              "action": None, "model": model, "cds": cds}

    drops = find_add_device_dropdowns(win)
    if len(drops) < 2:
        result["action"] = f"dropdown_not_found (n={len(drops)})"; return result
    target_drop = drops[1] if slave else drops[0]

    # 1. DropDownPart 클릭
    try:
        target_drop[0].click_input()
        time.sleep(1.5)
    except Exception as e:
        result["action"] = f"dropdown_click_exception: {e}"; return result

    # Slave dropdown: 3 컬럼 (Device / Functional Version), family·cds 없음
    # Master dropdown: 4 컬럼 (Product family / Device / Functional Version / CODESYS Version)
    if not slave:
        # 2. Product family
        fam = family or infer_family(model)
        if not fam:
            send_keys("{ESC}")
            result["action"] = f"family_inference_failed model={model}"; return result
        if not select_column_item(win, COLUMN_X["family"], fam):
            send_keys("{ESC}")
            result["action"] = f"family_not_found '{fam}'"; return result
        time.sleep(1.5)  # Device 컬럼 동적 로드 대기

    # 3. Device (model) — 정확 일치 → prefix → contains 매칭 fallback
    device_col = COLUMN_X["device"] if not slave else (326, 509)
    if not select_column_item(win, device_col, model, timeout=4.0):
        if not _select_column_item_startswith(win, device_col, model, timeout=2.0):
            if not _select_column_item_contains(win, device_col, model, timeout=2.0):
                send_keys("{ESC}")
                result["action"] = f"device_not_found '{model}'"; return result

    # 4. Functional Version (기본 첫 항목) — Slave는 List.left=509
    func_col = COLUMN_X["func"] if not slave else (508, 625)
    time.sleep(1.0)  # Device 선택 후 Functional Version 렌더 대기
    if not select_first_in_column(win, func_col, timeout=4.0):
        send_keys("{ESC}")
        result["action"] = "func_version_not_found"; return result

    # 5. CODESYS Version (master만)
    if not slave:
        if not select_column_item(win, COLUMN_X["cds"], cds):
            send_keys("{ESC}")
            result["action"] = f"cds_not_found '{cds}'"; return result

    # 6. 디바이스가 자동 추가됨 (별도 OK 버튼 없음)
    time.sleep(2.0)
    result["ok"] = True
    result["action"] = f"add_{'slave_' if slave else ''}device {model}/{cds}/{fam}"
    return result
