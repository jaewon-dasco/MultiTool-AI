"""NETWORK 노드 속성 변경 — 좌측 패널 수직 레이아웃 핸들러.

흐름:
  1. Network Editor 탭에서 NETWORK<n> Hyperlink invoke → 노드 선택
  2. 좌측 패널에 Name(Edit) / Bit Rate(ComboBox) / Devices(list) 노출
  3. 라벨 아래(y+18~25) 인접 컨트롤로 ComboBox.click_input + 값 선택

주요 속성:
  - Name (Edit)
  - Bit Rate (ComboBox: "125 kbit/s", "250 kbit/s", "500 kbit/s", "1000 kbit/s")
"""
import time
from pywinauto import mouse
from pywinauto.keyboard import send_keys
from . import common


def select_network(win, name: str = "NETWORK1") -> bool:
    """Network Editor 탭에서 NETWORK<n> Hyperlink invoke."""
    common.deselect_diagram(win)
    time.sleep(0.3)
    for h in win.descendants(control_type="Hyperlink"):
        try:
            if h.window_text() == name:
                h.invoke()
                time.sleep(1.5)
                return True
        except Exception: pass
    return False


def find_label_below_control(win, label_text: str, ctrl_types=("ComboBox", "Edit"),
                              max_dy: int = 30, x_overlap_min: int = 50) -> tuple:
    """라벨 Text 바로 아래의 컨트롤 찾기 (수직 레이아웃).
    반환: (control, kind) 또는 (None, None)."""
    label_rect = None
    for t in win.descendants(control_type="Text"):
        try:
            if t.window_text().strip() == label_text:
                label_rect = t.rectangle(); break
        except Exception: pass
    if not label_rect: return None, None

    best = None; best_kind = None; best_dy = 99999
    for kind in ctrl_types:
        for c in win.descendants(control_type=kind):
            try:
                r = c.rectangle()
                # 라벨 바로 아래 (y_top > label_bottom and dy < max_dy)
                dy = r.top - label_rect.bottom
                if dy < 0 or dy > max_dy: continue
                # x 겹침 확인
                overlap = min(r.right, label_rect.right) - max(r.left, label_rect.left)
                if overlap < x_overlap_min: continue
                if dy < best_dy:
                    best_dy = dy; best = c; best_kind = kind
            except Exception: pass
    return best, best_kind


def set_network_bitrate(win, network_name: str, value: str) -> dict:
    """NETWORK<n> 노드 선택 → Bit Rate ComboBox에서 value 선택.

    value 예: "500" (kbit/s 자동 매칭) 또는 "500 kbit/s" (정확 매칭).
    """
    result = {"ok": False, "kind": "network_property", "action": None,
              "network": network_name, "value": value}

    if not select_network(win, network_name):
        result["action"] = f"select_network_failed name={network_name}"; return result

    combo, kind = find_label_below_control(win, "Bit Rate", ctrl_types=("ComboBox",))
    if combo is None:
        result["action"] = "bitrate_combo_not_found"; return result

    try:
        combo.click_input()
        time.sleep(0.8)
        # 드롭다운 항목들이 ListItem으로 나타남
        v_lo = value.lower().strip()
        items = []
        for it in win.descendants(control_type="ListItem"):
            try:
                txt = (it.window_text() or "").strip()
                if v_lo in txt.lower():
                    items.append((it, txt))
            except Exception: pass
        if items:
            # 첫 번째 매칭 선택
            it, txt = items[0]
            it.click_input()
            time.sleep(0.5)
            result["ok"] = True
            result["action"] = f"network.bitrate.select '{txt}' @ {network_name}"
            return result
        # fallback: type + Enter
        send_keys(value, with_spaces=True); time.sleep(0.2)
        send_keys("{ENTER}"); time.sleep(0.4)
        result["ok"] = True
        result["action"] = f"network.bitrate.type_search val={value!r} @ {network_name}"
        return result
    except Exception as e:
        result["action"] = f"exception: {e}"
        return result
