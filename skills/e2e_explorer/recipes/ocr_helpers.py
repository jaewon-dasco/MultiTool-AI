"""OCR-based UI manipulation helpers for MultiTool's WPF Configure panel.

Used by all night-cycle recipes for fields that UI Automation doesn't expose.
"""
import time
import re
import hashlib
import shutil
from pathlib import Path
from PIL import ImageGrab, Image
from pywinauto import mouse, Desktop, Application
from pywinauto.keyboard import send_keys
import winocr

DEFAULT_OFFSET_X = 100  # 라벨 right edge 에서 우측 입력 위치까지의 평균 거리
PROJ_DIR = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject")


def system_export(timeout: float = 8.0) -> dict:
    """PROJECT → System Export (Ctrl+Alt+E) 트리거. .exp 파일 갱신.
    Returns {ok, dialog_handled, exp_files: [{name, sha, size}]}.
    """
    send_keys("^%e")
    time.sleep(2)
    # 다이얼로그가 뜨면 Enter 처리
    dialog_handled = False
    for w in Desktop(backend="win32").windows():
        try:
            t = w.window_text() or ""
            if any(k in t for k in ("Export", "Confirm", "Complete")):
                if t != "DasDemoProject - MultiTool Creator 8.4":
                    send_keys("{ENTER}")
                    time.sleep(1.5)
                    dialog_handled = True
                    break
        except Exception: pass
    time.sleep(timeout - 3 if not dialog_handled else 0.5)

    exp_files = []
    for p in PROJ_DIR.rglob("*.exp"):
        try:
            exp_files.append({
                "name": str(p.relative_to(PROJ_DIR)),
                "sha": hashlib.sha256(p.read_bytes()).hexdigest()[:16],
                "size": p.stat().st_size,
                "mtime": p.stat().st_mtime,
            })
        except Exception: pass
    return {"ok": True, "dialog_handled": dialog_handled, "exp_files": exp_files}


def snapshot_exp_state() -> dict:
    """현재 .exp 파일 상태 스냅샷 (sha+size+mtime). 후속 diff 비교용."""
    out = {}
    for p in PROJ_DIR.rglob("*.exp"):
        try:
            out[str(p.relative_to(PROJ_DIR))] = {
                "sha": hashlib.sha256(p.read_bytes()).hexdigest()[:16],
                "size": p.stat().st_size,
                "path": str(p),
            }
        except Exception: pass
    return out


def backup_exp_state(backup_dir: Path) -> dict:
    """모든 .exp 파일을 backup_dir로 복사 + 메타 반환."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    for p in PROJ_DIR.rglob("*.exp"):
        rel = str(p.relative_to(PROJ_DIR))
        dst = backup_dir / rel.replace("\\", "_").replace("/", "_")
        shutil.copy(p, dst)
        out[rel] = {"sha": hashlib.sha256(p.read_bytes()).hexdigest()[:16],
                    "size": p.stat().st_size, "backup": str(dst)}
    return out


def restore_exp_state(backup_meta: dict) -> int:
    """backup_meta의 .exp 파일들을 원래 위치로 복원. 갯수 반환."""
    n = 0
    for rel, info in backup_meta.items():
        src = Path(info["backup"])
        dst = PROJ_DIR / rel
        if src.exists():
            shutil.copy(src, dst)
            n += 1
    # 백업에 없던 파일은 삭제 (잔존 .exp 정리)
    backup_names = set(backup_meta.keys())
    for p in PROJ_DIR.rglob("*.exp"):
        rel = str(p.relative_to(PROJ_DIR))
        if rel not in backup_names:
            try: p.unlink()
            except Exception: pass
    return n


def diff_exp_state(before: dict, after: list) -> dict:
    """before(snapshot_exp_state result) vs after(system_export result['exp_files']) diff."""
    after_dict = {e["name"]: e for e in after}
    out = {"added": [], "removed": [], "changed": [], "unchanged": []}
    all_names = set(before) | set(after_dict)
    for name in sorted(all_names):
        b = before.get(name); a = after_dict.get(name)
        if not b: out["added"].append({"name": name, "size": a["size"]})
        elif not a: out["removed"].append({"name": name})
        elif b["sha"] != a["sha"]:
            out["changed"].append({"name": name, "size_delta": a["size"] - b["size"],
                                   "sha_before": b["sha"][:12], "sha_after": a["sha"][:12]})
        else:
            out["unchanged"].append(name)
    return out


def ocr_screen() -> list[dict]:
    """전체 화면 캡처 + OCR. 각 라인: {text, x, y, right, bottom, yc, w, h}."""
    img = ImageGrab.grab()
    r = winocr.recognize_pil_sync(img, lang="en-US")
    out = []
    for ln in r.get("lines", []):
        words = ln.get("words", [])
        if not words: continue
        xs = [w["bounding_rect"]["x"] for w in words]
        ys = [w["bounding_rect"]["y"] for w in words]
        xe = [w["bounding_rect"]["x"] + w["bounding_rect"]["width"] for w in words]
        ye = [w["bounding_rect"]["y"] + w["bounding_rect"]["height"] for w in words]
        out.append({"text": ln["text"].strip(),
                    "x": int(min(xs)), "y": int(min(ys)),
                    "right": int(max(xe)), "bottom": int(max(ye)),
                    "yc": int((min(ys)+max(ye))//2), "xc": int((min(xs)+max(xe))//2),
                    "w": int(max(xe) - min(xs)), "h": int(max(ye) - min(ys))})
    return out


def find_label(ocr_items, label_target: str, region: dict = None):
    """라벨 정확/부분 매칭. region={x_min,x_max,y_min,y_max}로 영역 제한 가능."""
    t = label_target.lower()
    def in_region(it):
        if not region: return True
        return (region.get("x_min", 0) <= it["x"] <= region.get("x_max", 99999) and
                region.get("y_min", 0) <= it["y"] <= region.get("y_max", 99999))
    items = [i for i in ocr_items if in_region(i)]
    exact = [i for i in items if i["text"].lower() == t]
    if exact:
        exact.sort(key=lambda i: (i["y"], i["x"]))
        return exact[0]
    contained = [i for i in items if t in i["text"].lower()]
    if contained:
        contained.sort(key=lambda i: len(i["text"]))
        return contained[0]
    return None


def click_right_of_label(label_item, offset_x: int = DEFAULT_OFFSET_X) -> tuple[int, int]:
    """라벨 right edge 에서 offset_x 만큼 우측 클릭."""
    cx = label_item["right"] + offset_x
    cy = label_item["yc"]
    mouse.click(coords=(cx, cy))
    time.sleep(0.3)
    return cx, cy


def set_numeric_field(label_target: str, value: str, offset_x: int = DEFAULT_OFFSET_X) -> bool:
    """NumericUpDown/TextBox 라벨 옆 클릭 → 전체 선택 → 새 값 입력 → Tab."""
    ocr = ocr_screen()
    item = find_label(ocr, label_target)
    if not item: return False
    click_right_of_label(item, offset_x)
    send_keys("^a"); time.sleep(0.1)
    send_keys("{DELETE}"); time.sleep(0.1)
    send_keys(value, with_spaces=True); time.sleep(0.2)
    send_keys("{TAB}"); time.sleep(0.5)
    return True


def set_text_field(label_target: str, value: str, offset_x: int = DEFAULT_OFFSET_X) -> bool:
    """TextBox (Application Version String 같은 자유 텍스트)."""
    return set_numeric_field(label_target, value, offset_x)


def toggle_checkbox(label_target: str, desired: bool = None, offset_x: int = -20) -> bool:
    """라벨 좌측 checkbox 클릭. offset_x 음수 = 좌측. desired 없으면 단순 토글."""
    ocr = ocr_screen()
    item = find_label(ocr, label_target)
    if not item: return False
    # 라벨 left edge - 20px 정도가 보통 체크박스 위치
    cx = item["x"] + offset_x
    cy = item["yc"]
    mouse.click(coords=(cx, cy))
    time.sleep(0.4)
    return True


def click_radio(option_target: str, region: dict = None) -> bool:
    """Radio option 라벨 좌측 클릭. (예: 'Slave' 또는 'Master')"""
    ocr = ocr_screen()
    item = find_label(ocr, option_target, region=region)
    if not item: return False
    # Radio button 마커는 라벨 left edge - 약 15px
    cx = item["x"] - 15
    cy = item["yc"]
    mouse.click(coords=(cx, cy))
    time.sleep(0.4)
    return True


def select_combo_value(label_target: str, value: str, offset_x: int = DEFAULT_OFFSET_X,
                       value_match: str = "startswith") -> bool:
    """ComboBox: 라벨 옆 클릭으로 드롭다운 열기 → 항목 OCR로 'value' 매칭 → 클릭.
    value_match: 'exact' | 'startswith' | 'contains'
    """
    ocr_before = ocr_screen()
    item = find_label(ocr_before, label_target)
    if not item: return False
    click_right_of_label(item, offset_x)
    time.sleep(0.8)  # dropdown animation

    # 드롭다운 항목들이 새로 떴음 - 다시 OCR
    ocr_after = ocr_screen()
    # 'value' 매칭 (기존 ocr에 없던 새 항목 우선)
    before_texts = {it["text"] for it in ocr_before}
    new_items = [it for it in ocr_after if it["text"] not in before_texts]
    v_lo = value.lower()
    def match(t):
        if value_match == "exact": return t == v_lo
        if value_match == "startswith": return t.startswith(v_lo)
        return v_lo in t
    candidates = [it for it in new_items if match(it["text"].lower())]
    if not candidates:
        # fallback: 전체 OCR에서 value 매칭
        candidates = [it for it in ocr_after if match(it["text"].lower())]
    if not candidates:
        # 마지막 fallback: keystrokes
        send_keys(value, with_spaces=True); time.sleep(0.2)
        send_keys("{ENTER}"); time.sleep(0.4)
        return True
    candidates.sort(key=lambda it: (it["y"], len(it["text"])))
    target = candidates[0]
    mouse.click(coords=(target["xc"], target["yc"]))
    time.sleep(0.5)
    return True


def detect_control_kind(label_target: str, offset_x: int = DEFAULT_OFFSET_X) -> dict:
    """라벨 옆 컨트롤을 클릭하고 화면 변화로 종류 자동 감지.

    Returns: {
        kind: 'combobox' | 'numeric_or_text' | 'unknown',
        label_item: dict | None,
        new_items: list[dict],   # 클릭으로 새로 나타난 OCR 라인들
        click_coords: tuple | None,
    }
    """
    ocr_before = ocr_screen()
    label_item = find_label(ocr_before, label_target)
    if not label_item:
        return {"kind": "unknown", "label_item": None, "new_items": [], "click_coords": None,
                "reason": "label not found"}
    coords = click_right_of_label(label_item, offset_x)
    time.sleep(0.8)  # 드롭다운 펼침 대기

    ocr_after = ocr_screen()
    before_texts = {it["text"] for it in ocr_before}
    new_items = [it for it in ocr_after if it["text"] not in before_texts]

    # 휴리스틱: 드롭다운 항목들은 보통 짧고, 클릭 위치 아래에 줄지어 등장
    short_below = [it for it in new_items
                   if len(it["text"]) <= 20 and it["y"] > coords[1] - 5]
    if len(short_below) >= 2:
        return {"kind": "combobox", "label_item": label_item, "new_items": new_items,
                "click_coords": coords, "dropdown_items": short_below}
    return {"kind": "numeric_or_text", "label_item": label_item, "new_items": new_items,
            "click_coords": coords}


def fuzzy_label_match(items: list, label_target: str, threshold: float = 0.4):
    """OCR 오인식 보완. label_target 단어 일부가 잡힌 라인 중 가장 가까운 것.

    label_target에 '|' 포함 시 alternatives로 분리 ('Bit Rate|ait Rate')."""
    candidates_target = label_target.split("|") if "|" in label_target else [label_target]
    overall_best = None; overall_score = 0
    for lt in candidates_target:
        t = lt.lower().strip()
        t_words = set(re.findall(r"\w+", t))
        for it in items:
            o = it["text"].lower()
            if t == o: return it
            if t in o:
                score = 0.9 + (len(t) / max(len(o), 1)) * 0.1
                if score > overall_score: overall_score = score; overall_best = it; continue
            o_words = set(re.findall(r"\w+", o))
            if not t_words: continue
            overlap = len(t_words & o_words) / len(t_words)
            # 글자 부분 일치 — last 2/3 chars (Bit Rate ↔ ait Rate, Send Receive ↔ end eceive)
            if overlap < 0.7:
                # 각 target word의 마지막 3글자가 OCR 라인 어디든 있으면 점수 가산
                tail_hits = 0; head_hits = 0
                for w in t_words:
                    if len(w) >= 3:
                        if any(w[-3:] in ow for ow in o_words): tail_hits += 1
                        if any(w[:3] in ow for ow in o_words): head_hits += 1
                if t_words:
                    char_score = max(tail_hits, head_hits) / len(t_words) * 0.75
                    overlap = max(overlap, char_score)
            if overlap > overall_score and overlap >= threshold:
                overall_score = overlap; overall_best = it
    return overall_best


def set_field_auto(label_target: str, value: str, offset_x: int = DEFAULT_OFFSET_X,
                   value_match: str = "startswith", expected_kind: str = None,
                   table_column: str = None) -> dict:
    """라벨 옆 컨트롤 종류별 액션 수행.

    expected_kind:
      - 'numeric_or_text': NumericUpDown/TextBox — Ctrl+A + value + Tab
      - 'combobox': 드롭다운 클릭 → 항목 OCR + 클릭
      - 'checkbox': 라벨 좌측 ~20px 클릭으로 토글
      - 'radio': 라벨 좌측 ~15px 클릭
      - None: 자동 감지 (detect_control_kind)

    table_column: 표 셀 진입 — row_marker=label, column_marker=table_column으로
    행/열 교차점 클릭 후 값 입력. label 우측 인접 컨트롤이 아닌 다른 열을 타겟할 때 사용.
    """
    result = {"ok": False, "kind": expected_kind, "action": None, "label": label_target, "value": value}

    # 표 셀 모드 — row(label) × column(table_column) 교차점 클릭
    if table_column:
        coords = click_table_cell(label_target, table_column)
        if not coords:
            result["kind"] = "unknown"; result["action"] = f"table_cell_not_found row={label_target!r} col={table_column!r}"
            return result
        time.sleep(0.5)
        if expected_kind == "combobox":
            # 셀 클릭 후 ComboBox 펼침 — value 항목 OCR + 클릭, 없으면 type+Enter
            ocr_after = ocr_screen()
            v_lo = value.lower()
            cands = [it for it in ocr_after if v_lo in it["text"].lower()]
            if cands:
                cands.sort(key=lambda it: it["y"])
                mouse.click(coords=(cands[0]["xc"], cands[0]["yc"]))
                time.sleep(0.5)
                result["ok"] = True; result["action"] = f"table.combobox '{cands[0]['text']}' @ row={label_target} col={table_column}"
                return result
            send_keys(value, with_spaces=True); time.sleep(0.2)
            send_keys("{ENTER}"); time.sleep(0.4)
            result["ok"] = True; result["action"] = f"table.combobox.type_search row={label_target} col={table_column}"
            return result
        # numeric_or_text (default for table cells)
        send_keys("^a"); time.sleep(0.1)
        send_keys("{DELETE}"); time.sleep(0.1)
        if value:
            send_keys(value, with_spaces=True); time.sleep(0.2)
        send_keys("{TAB}"); time.sleep(0.4)
        result["kind"] = "numeric_or_text"
        result["ok"] = True; result["action"] = f"table.numeric.tab_commit val={value!r} row={label_target} col={table_column}"
        return result

    ocr = ocr_screen()
    item = fuzzy_label_match(ocr, label_target)
    if not item:
        result["kind"] = "unknown"; result["action"] = "label_not_found"
        return result

    # Kind별 분기
    if expected_kind == "checkbox":
        # 라벨 좌측 ~20px가 체크박스
        cx = item["x"] - 20; cy = item["yc"]
        mouse.click(coords=(cx, cy))
        time.sleep(0.4)
        result["ok"] = True; result["action"] = f"checkbox.toggle @({cx},{cy})"
        return result

    if expected_kind == "radio":
        cx = item["x"] - 15; cy = item["yc"]
        mouse.click(coords=(cx, cy))
        time.sleep(0.4)
        result["ok"] = True; result["action"] = f"radio.select @({cx},{cy})"
        return result

    if expected_kind == "combobox":
        # 클릭으로 드롭다운 열기
        cx = item["right"] + offset_x; cy = item["yc"]
        mouse.click(coords=(cx, cy))
        time.sleep(0.8)
        ocr_after = ocr_screen()
        before_texts = {it["text"] for it in ocr}
        new_items = [it for it in ocr_after if it["text"] not in before_texts]
        v_lo = value.lower()
        def m(t):
            tl = t.lower()
            if value_match == "exact": return tl == v_lo
            if value_match == "startswith": return tl.startswith(v_lo)
            return v_lo in tl
        cands = [it for it in new_items if m(it["text"])]
        if cands:
            cands.sort(key=lambda it: (it["y"], len(it["text"])))
            tgt = cands[0]
            mouse.click(coords=(tgt["xc"], tgt["yc"]))
            time.sleep(0.5)
            result["ok"] = True; result["action"] = f"combobox.click '{tgt['text']}'"
            return result
        send_keys(value, with_spaces=True); time.sleep(0.2)
        send_keys("{ENTER}"); time.sleep(0.4)
        result["ok"] = True; result["action"] = "combobox.type_search"
        return result

    # default: numeric_or_text (또는 None → numeric으로)
    cx = item["right"] + offset_x; cy = item["yc"]
    mouse.click(coords=(cx, cy))
    time.sleep(0.3)
    send_keys("^a"); time.sleep(0.1)
    send_keys("{DELETE}"); time.sleep(0.1)
    if value:
        send_keys(value, with_spaces=True); time.sleep(0.2)
    send_keys("{TAB}"); time.sleep(0.4)
    result["kind"] = "numeric_or_text"
    result["ok"] = True; result["action"] = f"numeric.tab_commit val={value!r}"
    return result


def click_table_cell(row_marker: str, column_marker: str, marker_offset_y: int = 0) -> tuple[int, int] | None:
    """표 셀 클릭. row_marker: 행을 식별하는 값(예: 'Temperature'),
    column_marker: 컬럼 헤더 텍스트(예: 'Minimum'). row의 y, column의 x 결합 클릭."""
    ocr = ocr_screen()
    row_item = find_label(ocr, row_marker)
    col_item = find_label(ocr, column_marker)
    if not row_item or not col_item:
        return None
    cx = col_item["xc"]
    cy = row_item["yc"] + marker_offset_y
    mouse.click(coords=(cx, cy))
    time.sleep(0.4)
    return cx, cy


def find_wpf_dialog(title: str, timeout: float = 5.0) -> dict | None:
    """Win32 backend로 WPF Dialog 찾기 → {hwnd, rect, app}."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            for w in Desktop(backend="win32").windows():
                try:
                    if w.window_text() == title:
                        return {"hwnd": w.handle, "rect": w.rectangle(), "window": w}
                except Exception: pass
        except Exception: pass
        time.sleep(0.3)
    return None


def click_dialog_button(dlg_info: dict, button_text: str) -> bool:
    """다이얼로그 안에서 OCR로 버튼 텍스트 찾아 클릭."""
    r = dlg_info["rect"]
    # 다이얼로그 영역만 캡처
    img = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom))
    res = winocr.recognize_pil_sync(img, lang="en-US")
    for ln in res.get("lines", []):
        if ln["text"].strip().lower() == button_text.lower():
            words = ln.get("words", [])
            if not words: continue
            xs = [w["bounding_rect"]["x"] for w in words]
            ys = [w["bounding_rect"]["y"] for w in words]
            xe = [w["bounding_rect"]["x"] + w["bounding_rect"]["width"] for w in words]
            ye = [w["bounding_rect"]["y"] + w["bounding_rect"]["height"] for w in words]
            # convert to screen coords
            cx = r.left + int((min(xs)+max(xe))//2)
            cy = r.top + int((min(ys)+max(ye))//2)
            mouse.click(coords=(cx, cy))
            time.sleep(0.6)
            return True
    return False


def ocr_region(left: int, top: int, right: int, bottom: int) -> list[dict]:
    """화면 특정 영역만 OCR. 우측 상세 패널 분리 분석용."""
    img = ImageGrab.grab(bbox=(left, top, right, bottom))
    res = winocr.recognize_pil_sync(img, lang="en-US")
    out = []
    for ln in res.get("lines", []):
        words = ln.get("words", [])
        if not words: continue
        xs = [w["bounding_rect"]["x"] for w in words]
        ys = [w["bounding_rect"]["y"] for w in words]
        xe = [w["bounding_rect"]["x"] + w["bounding_rect"]["width"] for w in words]
        ye = [w["bounding_rect"]["y"] + w["bounding_rect"]["height"] for w in words]
        out.append({"text": ln["text"].strip(),
                    "x": left + int(min(xs)), "y": top + int(min(ys)),
                    "right": left + int(max(xe)), "bottom": top + int(max(ye)),
                    "yc": top + int((min(ys)+max(ye))//2),
                    "xc": left + int((min(xs)+max(xe))//2)})
    return out


def get_right_panel_region(win) -> tuple[int, int, int, int]:
    """Configure 패널의 우측 영역 좌표 추정. 보통 화면 가운데 분리선부터 오른쪽."""
    r = win.rectangle()
    # 좌측 패널 폭 ~200 + 메인 컨텐츠 폭 가변. 우측 패널은 보통 화면 가운데부터.
    mid_x = r.left + int(r.width() * 0.4)  # 화면 40% 지점부터 우측
    return (mid_x, r.top + 100, r.right, r.bottom - 50)


def click_toolbar_button(win, button_label: str, search_region: dict = None) -> bool:
    """toolbar의 라벨 가진 버튼 클릭. button_label은 hover tooltip 또는 인근 text."""
    # 1. UIA Button 중 이름 일치 우선
    for b in win.descendants(control_type="Button"):
        try:
            if b.window_text() == button_label or button_label.lower() in b.window_text().lower():
                b.click_input(); time.sleep(0.5)
                return True
        except Exception: pass
    # 2. OCR로 라벨 찾고 클릭
    ocr = ocr_screen()
    item = fuzzy_label_match(ocr, button_label, threshold=0.5)
    if item:
        mouse.click(coords=(item["xc"], item["yc"]))
        time.sleep(0.5)
        return True
    return False


def click_table_row(row_marker_text: str, click_offset: tuple = (0, 0)) -> tuple[int, int] | None:
    """표의 행에서 row_marker_text 찾아 클릭. click_offset = (dx, dy) for column 위치."""
    ocr = ocr_screen()
    item = fuzzy_label_match(ocr, row_marker_text)
    if not item: return None
    cx = item["xc"] + click_offset[0]
    cy = item["yc"] + click_offset[1]
    mouse.click(coords=(cx, cy))
    time.sleep(0.5)
    return cx, cy


def click_expand_arrow_near(row_marker_text: str, arrow_offset_x: int = -30) -> bool:
    """표 행의 ▶ expand 화살표 클릭. row_marker_text는 그 행의 텍스트, 화살표는 보통 -30px 좌측."""
    ocr = ocr_screen()
    item = fuzzy_label_match(ocr, row_marker_text)
    if not item: return False
    mouse.click(coords=(item["x"] + arrow_offset_x, item["yc"]))
    time.sleep(0.6)
    return True


def fill_dialog_form(dlg_info: dict, fields: dict) -> dict:
    """다이얼로그 안 입력 필드들을 OCR + 클릭 + 입력 채움.
    fields: {"Index": "2500", "Name": "TestVar", "DataType": "BYTE"}
    Returns: {filled: int, missing: list[str]}
    """
    items = ocr_dialog_form(dlg_info)
    filled = 0; missing = []
    for label, value in fields.items():
        # 다이얼로그 안에서 라벨 찾기
        target = None
        for it in items:
            if label.lower() in it["text"].lower():
                target = it; break
        if not target:
            missing.append(label); continue
        # 라벨 우측 입력 영역 클릭
        click_x = target["right"] + 80
        click_y = target["yc"]
        mouse.click(coords=(click_x, click_y))
        time.sleep(0.3)
        send_keys("^a"); send_keys("{DELETE}")
        send_keys(value, with_spaces=True)
        send_keys("{TAB}")
        time.sleep(0.3)
        filled += 1
    return {"filled": filled, "missing": missing}


def ocr_dialog_form(dlg_info: dict) -> list[dict]:
    """다이얼로그 안 OCR (screen-relative 좌표 변환)."""
    r = dlg_info["rect"]
    img = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom))
    res = winocr.recognize_pil_sync(img, lang="en-US")
    out = []
    for ln in res.get("lines", []):
        words = ln.get("words", [])
        if not words: continue
        xs = [w["bounding_rect"]["x"] for w in words]
        ys = [w["bounding_rect"]["y"] for w in words]
        xe = [w["bounding_rect"]["x"] + w["bounding_rect"]["width"] for w in words]
        ye = [w["bounding_rect"]["y"] + w["bounding_rect"]["height"] for w in words]
        out.append({"text": ln["text"].strip(),
                    "x": r.left + int(min(xs)),
                    "y": r.top + int(min(ys)),
                    "right": r.left + int(max(xe)),
                    "bottom": r.top + int(max(ye)),
                    "yc": r.top + int((min(ys)+max(ye))//2),
                    "xc": r.left + int((min(xs)+max(xe))//2)})
    return out
