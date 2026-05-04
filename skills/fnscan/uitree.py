"""uitree.py — MultiTool 실행 및 UIA 메뉴 트리 덤프"""

import json
import time
from pathlib import Path

MT_EXE_PATTERN = r"C:\Program Files (x86)\Epec\MultiTool Creator {ver}\MultiTool.exe"
DEMO_DIR       = Path(__file__).parent.parent.parent / "DemoProject" / "ScanDemo"
DEMO_PROJECT   = DEMO_DIR / "ScanDemo.mtproject"


def dump_ui_tree(ver: str, out_path: Path):
    """MultiTool 실행 → 메뉴바 + 컨텍스트 메뉴 수집 → JSON 저장"""
    try:
        from pywinauto import Application
    except ImportError:
        print("  [WARN] pywinauto 미설치 — UIA 트리 덤프 skip")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("{}")
        return

    exe = MT_EXE_PATTERN.format(ver=ver)

    # 1단계: 빈 앱 실행 → 메뉴바 수집
    app = Application(backend="uia").start(exe)
    win = _wait_main_window(app)
    tree = _collect_menus(app, win)
    close_app(app, win)
    time.sleep(1)

    # 2단계: 스캔용 데모 프로젝트 생성 → 컨텍스트 메뉴 수집
    app2 = Application(backend="uia").start(exe)
    win2 = _wait_main_window(app2)
    try:
        _create_demo_project(app2, win2)
        time.sleep(2)
        ctx = _collect_context_menus(app2, win2)
        tree["context_menus"] = ctx
    except Exception as e:
        print(f"  [WARN] 컨텍스트 메뉴 수집 실패: {e}")
        tree["context_menus"] = {}
    finally:
        close_app(app2, win2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")


# ── WindowSpec 변환 헬퍼 ──────────────────────────────────────────────────────
def _as_spec(app, w):
    """UIAWrapper → WindowSpecification 변환 (child_window 사용 가능하게)"""
    try:
        return app.window(handle=w.handle)
    except Exception:
        return w


# ── 앱 종료 (Alt+F4) ──────────────────────────────────────────────────────────
def close_app(app, win):
    """Alt+F4로 MultiTool 정상 종료. 저장 확인 다이얼로그는 닫지 않음으로 처리."""
    from pywinauto import keyboard
    try:
        win.set_focus()
        keyboard.send_keys("%{F4}")
        time.sleep(1)
        # 저장 여부 다이얼로그 대응 — '저장 안 함' or 'Don't Save' 클릭
        top = app.top_window()
        name = top.element_info.name or ""
        if name != win.element_info.name:
            for btn in top.descendants(control_type="Button"):
                lbl = (btn.element_info.name or "").lower()
                if any(k in lbl for k in ("저장 안", "don't save", "discard", "no")):
                    btn.click_input()
                    break
            else:
                keyboard.send_keys("{TAB}{ENTER}")
        time.sleep(0.5)
    except Exception:
        pass


# ── 데모 프로젝트 생성 ────────────────────────────────────────────────────────
def _create_demo_project(app, win):
    """기존 ScanDemo 폴더 삭제 → New Project 생성 → CU-3606-21 디바이스 추가 → 저장"""
    import shutil
    from pywinauto import keyboard

    # 기존 프로젝트 강제 삭제 (락 파일 포함)
    if DEMO_DIR.exists():
        import subprocess
        subprocess.run(["cmd", "/c", "rd", "/s", "/q", str(DEMO_DIR)],
                       capture_output=True)
        time.sleep(0.5)
        if DEMO_DIR.exists():
            shutil.rmtree(DEMO_DIR, ignore_errors=True)
    DEMO_DIR.parent.mkdir(parents=True, exist_ok=True)

    # FILE > New Project
    _open_menu_item(app, win, 0, "New Project")
    time.sleep(1)

    # New Project 다이얼로그
    dlg = _as_spec(app, _find_dialog(app, "NewProjectDialog"))

    # 1단계: Browse로 경로 먼저 지정
    browse_clicked = False
    try:
        for btn in dlg.descendants(control_type="Button"):
            lbl = (btn.element_info.name or "").lower()
            if "browse" in lbl or lbl == "...":
                btn.click_input()
                browse_clicked = True
                time.sleep(1.5)
                break
    except Exception as e:
        print(f"  [WARN] Browse 버튼 탐색 실패: {e}")

    if browse_clicked:
        _browse_select_folder(app, win, DEMO_DIR.parent)
    else:
        print("  [WARN] Browse 버튼 미발견 — 직접 타이핑 fallback")
        edits = dlg.children(control_type="Edit")
        edits[1].click_input()
        keyboard.send_keys("^a")
        keyboard.send_keys(str(DEMO_DIR.parent), with_spaces=True)
        time.sleep(0.3)

    time.sleep(0.5)

    # 2단계: 프로젝트명 입력
    edits = dlg.children(control_type="Edit")
    edits[0].click_input()
    time.sleep(0.2)
    keyboard.send_keys("^a")
    keyboard.send_keys("ScanDemo", with_spaces=True)
    time.sleep(0.3)

    # 3단계: Create Project
    dlg.child_window(auto_id="NewProjectDialog_CreateProjectButton").click_input()
    print("  [OK] New Project 생성")
    time.sleep(6)

    # Add Device — CU-3606-21
    _add_device_3606(app, win)

    # DeviceSelector 팝업이 완전히 닫힐 때까지 대기 후 저장
    deadline = time.time() + 5
    while time.time() < deadline:
        time.sleep(0.3)
        popup_open = any(
            not (c.element_info.name or "") and c.element_info.control_type == "Window"
            for c in win.children()
        )
        if not popup_open:
            break

    win.set_focus()
    keyboard.send_keys("^s")
    time.sleep(1)
    print("  [OK] 프로젝트 저장")


def _browse_select_folder(app, win, target_parent: Path):
    """폴더 선택 다이얼로그: 부모 폴더로 이동 → 대상 폴더 더블클릭 → 폴더 선택"""
    from pywinauto import keyboard

    # 폴더 선택 창 찾기 (win 하위 Window 자식)
    folder_win = None
    deadline = time.time() + 6
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            for child in win.descendants():
                if child.element_info.control_type == "Window":
                    name = child.element_info.name or ""
                    if "폴더" in name or "folder" in name.lower():
                        folder_win = child
                        break
        except Exception:
            pass
        if folder_win:
            break

    if folder_win is None:
        print("  [WARN] 폴더 선택 창 미발견")
        return

    fw = _as_spec(app, folder_win)  # UIAWrapper → WindowSpecification

    # 1단계: 폴더: 편집 필드(id=1152)에 대상 경로 직접 입력 → Enter
    try:
        addr = fw.child_window(auto_id="1152", control_type="Edit")
        addr.click_input()
        time.sleep(0.2)
        keyboard.send_keys("^a")
        keyboard.send_keys(str(target_parent), with_spaces=True)
        time.sleep(0.2)
        keyboard.send_keys("{ENTER}")
        time.sleep(1.5)
        print(f"  [OK] 폴더 이동: {target_parent}")
    except Exception as e:
        print(f"  [WARN] 주소 입력 실패: {e}")
        return

    # 2단계: 폴더 선택 버튼 클릭
    try:
        ok_btn = fw.child_window(auto_id="1", control_type="Button")
        ok_btn.click_input()
        time.sleep(0.5)
        print("  [OK] 폴더 선택 완료")
    except Exception as e:
        print(f"  [WARN] 폴더 선택 버튼 실패: {e}")
        keyboard.send_keys("{ENTER}")
        time.sleep(0.5)


def _add_device_3606(app, win):
    """Network Editor Add Device → DeviceSelector 팝업 → CU-3606-21 선택"""
    from pywinauto import keyboard

    # 1단계: Add Device 버튼 클릭
    try:
        add_btn = win.child_window(auto_id="NetworkEditorView_AddDeviceButton")
        btn_part = add_btn.child_window(auto_id="ButtonPart", control_type="Button")
        btn_part.click_input()
        print("  [OK] Add Device 클릭")
    except Exception as e:
        print(f"  [WARN] Add Device 버튼 실패: {e}")
        return

    time.sleep(2.5)

    # 2단계: 팝업 Window → DeviceSelector 찾기
    selector = None
    deadline = time.time() + 10
    while time.time() < deadline:
        time.sleep(0.3)
        try:
            # 이름 없는 Window 팝업 먼저 탐색
            popup = None
            for child in win.children():
                if child.element_info.control_type == "Window" and not (child.element_info.name or ""):
                    popup = child; break
            src = popup if popup else win
            for child in src.descendants():
                if child.element_info.automation_id == "DeviceSelector":
                    selector = child; break
        except Exception:
            pass
        if selector:
            break

    if selector is None:
        print("  [WARN] DeviceSelector 미발견")
        keyboard.send_keys("{ESC}")
        return

    def _get_selector():
        """DeviceSelector UIAWrapper 재탐색 (stale 방지)"""
        for child in win.children():
            if child.element_info.control_type == "Window" and not (child.element_info.name or ""):
                for d in child.descendants():
                    if (d.element_info.automation_id or "") == "DeviceSelector":
                        return d
        for d in win.descendants():
            if (d.element_info.automation_id or "") == "DeviceSelector":
                return d
        return None

    def _find_list(selector_uia, auto_id):
        """UIAWrapper 하위에서 auto_id 일치 List 반환"""
        try:
            for elem in selector_uia.descendants(control_type="List"):
                if (elem.element_info.automation_id or "") == auto_id:
                    return elem
        except Exception:
            pass
        return None

    def _hover_item(item):
        """UIA 요소 위로 실제 마우스 커서 이동 (WPF hover 트리거)"""
        try:
            import pyautogui
            rect = item.rectangle()
            cx = (rect.left + rect.right) // 2
            cy = (rect.top + rect.bottom) // 2
            pyautogui.moveTo(cx, cy, duration=0.3)
        except Exception:
            item.move_mouse_input()

    def _wait_list_items(lst_uia, timeout=4.0) -> list:
        """리스트 항목이 로드될 때까지 대기"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                items = [i for i in lst_uia.descendants(control_type="ListItem")]
                if items:
                    return items
            except Exception:
                pass
            time.sleep(0.4)
        return []

    def _hover_select(lst_uia, keyword, label_hint, hover=False):
        """UIAWrapper List에서 keyword 포함 항목 hover/클릭"""
        if lst_uia is None:
            print(f"  [WARN] {label_hint} 리스트 없음")
            return None
        try:
            items = _wait_list_items(lst_uia)
            for item in items:
                lbl = _get_list_item_label(item)
                if keyword.lower() in lbl.lower():
                    if hover:
                        _hover_item(item)
                    else:
                        item.click_input()
                    time.sleep(1.2)
                    print(f"  [OK] {label_hint}: '{lbl}'")
                    return item
            lbls = [_get_list_item_label(i) for i in items]
            print(f"  [WARN] {label_hint} '{keyword}' 미발견 (항목: {lbls})")
        except Exception as e:
            print(f"  [WARN] {label_hint} 선택 실패: {e}")
        return None

    # 3단계: ProductFamily "3000" 클릭 → Device 목록 동적 로드 대기
    sel = _get_selector()
    pf_list = _find_list(sel, "ProductFamily") if sel else None
    if not _hover_select(pf_list, "3000", "ProductFamily", hover=False):
        keyboard.send_keys("{ESC}"); return

    # 4단계: Device "3606" 클릭 → FunctionalVersion 목록 동적 로드 대기
    sel = _get_selector()
    dev_list = _find_list(sel, "MainView_DeviceListView") if sel else None
    if not _hover_select(dev_list, "3606", "Device", hover=False):
        keyboard.send_keys("{ESC}"); return

    # 5단계: FunctionalVersion "3606-21" 클릭 → CodesysVersion 목록 동적 로드 대기
    sel = _get_selector()
    fv_list = _find_list(sel, "MainView_FunctionalVersionListView") if sel else None
    if not _hover_select(fv_list, "3606-21", "FunctionalVersion", hover=False):
        keyboard.send_keys("{ESC}"); return

    # 6단계: CODESYS Version "2.3" 클릭 (팝업 자동 닫히는 경우 skip)
    sel = _get_selector()
    cv_list = _find_list(sel, "MainView_CodesysVersionListView") if sel else None
    _hover_select(cv_list, "2.3", "CodesysVersion", hover=False)

    time.sleep(1.5)
    print("  [OK] 디바이스 추가 완료")


def _get_list_item_label(item) -> str:
    """ListItem 표시 텍스트 추출 (ViewModel 이름 대신 Text 자식 참조)"""
    name = item.element_info.name or ""
    if name and not name.startswith("System."):
        return name
    try:
        for child in item.descendants(control_type="Text"):
            t = (child.element_info.name or "").strip()
            if t:
                return t
    except Exception:
        pass
    return name


# ── 메인 창 대기 ─────────────────────────────────────────────────────────────
def _wait_main_window(app):
    deadline = time.time() + 30
    while time.time() < deadline:
        time.sleep(2)
        try:
            w = app.top_window()
            name = w.element_info.name or ""
            if "DynamicSplashScreen" not in name:
                time.sleep(3)
                return app.top_window()  # fresh
        except Exception:
            pass
    print("  [WARN] 메인 창 대기 시간 초과")
    return app.top_window()


# ── 메뉴 항목 클릭 ────────────────────────────────────────────────────────────
def _open_menu_item(app, win, top_idx: int, label: str):
    """탑레벨 메뉴[top_idx] 클릭 → 팝업에서 label 항목 클릭"""
    from pywinauto import keyboard

    try:
        win = app.top_window()  # stale handle 방지
    except Exception:
        pass
    win.set_focus()
    time.sleep(0.3)
    menu = win.child_window(control_type="Menu")
    top_items = menu.children(control_type="MenuItem")
    top_items[top_idx].click_input()
    time.sleep(0.8)

    # app.windows() 우선 — 팝업이 별도 창으로 열리는 경우 포함
    for w in app.windows():
        try:
            for elem in w.descendants(control_type="MenuItem"):
                if _get_label(elem) == label:
                    elem.click_input()
                    return
        except Exception:
            pass

    # fallback: win.descendants
    try:
        for elem in win.descendants(control_type="MenuItem"):
            if _get_label(elem) == label:
                elem.click_input()
                return
    except Exception:
        pass

    keyboard.send_keys("{ESC}")
    raise RuntimeError(f"메뉴 항목 '{label}' 없음")


def _all_menu_items(app, win):
    """현재 열린 팝업 포함 전체 MenuItem 열거"""
    seen_ids = set()
    elems = []
    sources = [win]
    try:
        sources += list(app.windows())
    except Exception:
        pass
    for src in sources:
        try:
            for e in src.descendants(control_type="MenuItem"):
                eid = id(e.element_info)
                if eid not in seen_ids:
                    seen_ids.add(eid)
                    elems.append(e)
        except Exception:
            pass
    return elems


# ── 다이얼로그 탐색 ───────────────────────────────────────────────────────────
def _find_dialog(app, auto_id_kw: str = "", keyword: str = "", timeout: float = 5) -> object:
    """auto_id 또는 이름에 keyword가 포함된 창 탐색"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            for w in app.windows():
                aid  = w.element_info.automation_id or ""
                name = w.element_info.name or ""
                if (auto_id_kw and auto_id_kw in aid) or \
                   (keyword and keyword in name):
                    return w
            # 메인 창 하위 Window 자식
            top = app.top_window()
            for child in top.children():
                if child.element_info.control_type == "Window":
                    aid  = child.element_info.automation_id or ""
                    name = child.element_info.name or ""
                    if (auto_id_kw and auto_id_kw in aid) or \
                       (keyword and keyword in name):
                        return child
                    return child  # keyword 없으면 첫 번째 자식 반환
        except Exception:
            pass
    return None


# ── 메뉴바 수집 ───────────────────────────────────────────────────────────────
def _collect_menus(app, win) -> dict:
    from pywinauto import keyboard

    try:
        win = app.top_window()
    except Exception:
        pass
    result = {"name": win.element_info.name, "items": []}
    try:
        win.set_focus()
        time.sleep(0.5)
        menu = win.child_window(control_type="Menu")
        top_items = menu.children(control_type="MenuItem")
    except Exception as e:
        print(f"  [WARN] 메뉴 탐색 실패: {e}")
        return result

    top_labels = {_get_label(i) for i in top_items}

    for item in top_items:
        label = _get_label(item)
        entry = {
            "name":          label,
            "shortcut":      "",
            "automation_id": item.element_info.automation_id,
            "children":      []
        }
        # 최대 2회 재시도
        for attempt in range(2):
            try:
                win.set_focus()
                time.sleep(0.4)
                item.click_input()
                time.sleep(1.0)
                entry["children"] = _collect_popup(app, top_labels)
                if entry["children"]:
                    break
            except Exception as e:
                if attempt == 1:
                    print(f"  [WARN] {label} 메뉴 열기 실패: {e}")
            finally:
                keyboard.send_keys("{ESC}")
                time.sleep(0.5)
        result["items"].append(entry)

    return result


def _collect_popup(app, top_labels: set) -> list:
    items = []
    seen  = set()
    sources = []
    try: sources += [w for w in app.windows()
                     if w.element_info.control_type in ("Window", "Popup", "Menu")]
    except Exception: pass
    if not sources:
        try: sources = [app.top_window()]
        except Exception: pass

    for src in sources:
        try:
            for elem in src.descendants(control_type="MenuItem"):
                label = _get_label(elem)
                if not label or label in top_labels or label in seen:
                    continue
                seen.add(label)
                rect = elem.rectangle()
                items.append({
                    "name":          label,
                    "shortcut":      _parse_shortcut(elem.element_info.name),
                    "automation_id": elem.element_info.automation_id,
                    "coordinates":   [(rect.left + rect.right) // 2,
                                      (rect.top + rect.bottom) // 2]
                })
        except Exception:
            pass
    return items


# ── 컨텍스트 메뉴 수집 ────────────────────────────────────────────────────────
def _collect_context_menus(app, win) -> dict:
    try:
        win = app.top_window()
        # 이전 실행에서 maximize 잔존 가능 — default 크기로 복원
        try:
            win.restore()
            time.sleep(1.0)
        except Exception: pass
        win = app.top_window()
    except Exception:
        pass
    result = {
        "device":         _rclick_collect(app, win, "device"),
        "device_toolbar": _collect_device_toolbar(app, win),
    }
    # device_config_tabs는 별도 키로 반환 (mapper에서 다른 처리)
    cfg_tabs = _collect_device_config_tabs(app, win)
    if cfg_tabs:
        result["_device_config"] = cfg_tabs
    return result


# ── 디바이스 Configuration 탭 스캔 ────────────────────────────────────────────
DEVICE_CONFIG_TABS = [
    ("CAN",               "CANSettingsViewRadTabItem",      ["CAN 1"]),
    ("CANopen",           "",                                []),
    ("J1939",             "DeviceConfigureView_TabJ1939",   []),
    ("NMEA 2000",         "DeviceConfigureView_NMEA2000",   []),
    ("Address Claiming",  "AddressClaimingViewRadTabItem",  []),
    ("Diagnostics",       "DiagnosticsViewRadTabItem",      []),
    ("Object Dictionary", "ObjectDictionaryViewRadTabItem", []),
    ("PDO",               "PDOViewRadTabItem",              []),
    ("I/O",               "IoViewRadTabItem",               []),
    ("Events",            "EventsViewRadTabItem",           []),
    ("ISOBUS",            "IsobusViewRadTabItem",           []),
    ("Library Manager",   "LibraryManagerViewRadTabItem",   []),
]


def _get_tab_label(tab):
    n = (tab.element_info.name or "").strip()
    if n and not n.startswith(("Telerik.", "Epec.MT.", "System.")):
        return n
    try:
        for c in tab.descendants(control_type="Text"):
            t = (c.element_info.name or "").strip()
            if t and not t.startswith(("Telerik.", "Epec.MT.", "System.")):
                return t
    except Exception:
        pass
    return n


def _find_config_tab(win, label, aid_kw):
    for elem in win.descendants(control_type="TabItem"):
        if _get_tab_label(elem).lower() == label.lower():
            return elem
        if aid_kw and aid_kw in (elem.element_info.automation_id or ""):
            return elem
    return None


def _scan_tab_inputs(win):
    inputs = []
    seen = set()
    for elem in win.descendants():
        try:
            ct = elem.element_info.control_type or ""
            if ct not in ("Edit", "ComboBox", "CheckBox", "Spinner", "RadioButton", "Slider"):
                continue
            aid = elem.element_info.automation_id or ""
            n   = elem.element_info.name or ""
            try:
                r = elem.rectangle()
                key = (ct, n, aid, r.left, r.top)
                rect = {"L": r.left, "T": r.top, "R": r.right, "B": r.bottom}
            except Exception:
                key = (ct, n, aid); rect = None
            if key in seen: continue
            seen.add(key)
            val = ""
            try:
                if ct == "Edit" and hasattr(elem, "get_value"):
                    val = elem.get_value()
                elif ct == "ComboBox" and hasattr(elem, "selected_text"):
                    val = elem.selected_text() or ""
                elif ct == "CheckBox":
                    try: val = "checked" if elem.get_toggle_state() else "unchecked"
                    except Exception: val = ""
            except Exception: val = ""
            inputs.append({
                "type":          ct,
                "name":          n,
                "automation_id": aid,
                "value":         str(val),
                "rect":          rect,
            })
        except Exception:
            pass
    return inputs


def _scan_tab_labels(win):
    labels = []
    for elem in win.descendants(control_type="Text"):
        try:
            n = (elem.element_info.name or "").strip()
            if not n or len(n) > 80: continue
            if n.startswith(("Telerik.", "Epec.MT.", "System.")): continue
            if n in ("FILE", "PROJECT", "HELP", "-", "+", "%"): continue
            labels.append(n)
        except Exception:
            pass
    return labels


def _collect_device_config_tabs(app, win) -> dict:
    """디바이스 Configure 진입 → 12개 설정 탭 순회 → 각 탭의 입력·라벨 수집"""
    from pywinauto.mouse import click
    import pyautogui

    result = {}
    try:
        ne_spec = win.child_window(auto_id="MainView_NetworkEditorView", control_type="Pane")
        ne = ne_spec.wrapper_object()
        pane = ne.rectangle()

        canvas_off = 53
        try:
            ab = win.child_window(auto_id="NetworkEditorView_AddDeviceButton").wrapper_object()
            canvas_off = (ab.rectangle().bottom - pane.top) + 10
        except Exception: pass

        dev_x = pane.left + (pane.width() // 4)
        dev_y = pane.top + canvas_off + 110

        # 디바이스 클릭 + Configure (default 크기에서 검증된 좌표)
        win.set_focus(); time.sleep(0.5)
        click(coords=(dev_x, dev_y))
        time.sleep(0.8)
        pyautogui.click(dev_x + 30, dev_y - 85)
        time.sleep(2.5)

        # Configuration view 열림 → 창 최대화
        win = app.top_window()
        try:
            win.maximize()
            time.sleep(1.5)
        except Exception: pass
        win = app.top_window()

        # 각 탭 스캔
        for label, aid_kw, sub_tabs in DEVICE_CONFIG_TABS:
            try:
                win = app.top_window()
                tab = _find_config_tab(win, label, aid_kw)
                if tab is None:
                    result[label] = {"error": "tab not found"}
                    continue
                tab.click_input()
                time.sleep(1.2)

                for sub_label in sub_tabs:
                    sub = _find_config_tab(win, sub_label, "")
                    if sub:
                        try: sub.click_input(); time.sleep(1.0)
                        except Exception: pass

                inputs = _scan_tab_inputs(win)
                labels = _scan_tab_labels(win)
                result[label] = {"inputs": inputs, "labels": labels}
                print(f"  [OK] {label}: inputs={len(inputs)} labels={len(labels)}")
            except Exception as e:
                print(f"  [WARN] {label} 스캔 실패: {e}")
                result[label] = {"error": str(e)}
    except Exception as e:
        print(f"  [WARN] device_config 수집 실패: {e}")
    return result


def _collect_device_toolbar(app, win) -> list:
    """디바이스 선택 시 나타나는 플로팅 툴바(🔧 Configure / 📦 Create CODESYS Project / ❌ Delete) 수집

    각 아이콘 위에 마우스를 올린 후 tooltip 텍스트를 수집한다."""
    items = []
    try:
        from pywinauto import keyboard
        from pywinauto.mouse import click
        import pyautogui

        ne_spec = win.child_window(auto_id="MainView_NetworkEditorView", control_type="Pane")
        ne = ne_spec.wrapper_object()
        pane_rect = ne.rectangle()

        canvas_top_offset = 0
        try:
            add_btn = win.child_window(auto_id="NetworkEditorView_AddDeviceButton").wrapper_object()
            canvas_top_offset = (add_btn.rectangle().bottom - pane_rect.top) + 10
        except Exception:
            pass

        rel_x = pane_rect.width() // 4
        rel_y = canvas_top_offset + 110
        dev_x = pane_rect.left + rel_x
        dev_y = pane_rect.top + rel_y

        win.set_focus(); time.sleep(0.3)
        click(coords=(dev_x, dev_y))
        time.sleep(0.8)

        # 툴바 sweep: 디바이스 본체 위로 이동(선택 유지)했다가 다음 hover
        # 아이콘 순서 — 🔧 Configure / 📦 Create CODESYS Project / ❌ Delete
        tb_y = dev_y - 85
        seen = set()
        for offset in range(-30, 145, 10):
            px = dev_x + offset
            try:
                # 디바이스 본체 위로 이동 → tooltip 리셋(선택은 유지)
                pyautogui.moveTo(dev_x, dev_y + 5, duration=0.05)
                time.sleep(0.25)
                pyautogui.moveTo(px, tb_y, duration=0.12)
                time.sleep(1.1)
                tooltip_text = ""
                try:
                    for elem in win.descendants(control_type="ToolTip"):
                        t = (elem.element_info.name or "").strip()
                        if t and t != "Add Device" and t not in seen:
                            tooltip_text = t; break
                except Exception:
                    pass
                if tooltip_text:
                    seen.add(tooltip_text)
                    items.append({
                        "name":          tooltip_text,
                        "shortcut":      "",
                        "automation_id": "",
                        "coordinates":   [px, tb_y]
                    })
                    print(f"  [OK] 디바이스 툴바: {tooltip_text} (offset={offset})")
                if len(items) >= 3:
                    break
            except Exception as e:
                print(f"  [WARN] hover offset={offset} 실패: {e}")
        # 선택 해제
        try:
            click(coords=(pane_rect.right - 50, pane_rect.bottom - 50))
        except Exception:
            pass
    except Exception as e:
        print(f"  [WARN] device_toolbar 수집 실패: {e}")
    return items


def _rclick_collect(app, win, target: str) -> list:
    """네트워크·디바이스 노드는 UIA 미노출 — Canvas 좌표 기반 우클릭"""
    from pywinauto import keyboard
    items = []
    try:
        # MainView_NetworkEditorView Pane = 네트워크 캔버스 (툴바 포함)
        ne_spec = win.child_window(auto_id="MainView_NetworkEditorView", control_type="Pane")
        ne = ne_spec.wrapper_object()
        pane_rect = ne.rectangle()

        # 캔버스 시작점 = Add Device 버튼 bottom + margin
        canvas_top_offset = 0
        try:
            add_btn_spec = win.child_window(auto_id="NetworkEditorView_AddDeviceButton")
            add_btn = add_btn_spec.wrapper_object()
            add_rect = add_btn.rectangle()
            canvas_top_offset = (add_rect.bottom - pane_rect.top) + 10
        except Exception:
            pass

        # 디바이스 박스 좌표 (단일 디바이스 레이아웃 가정)
        rel_x = pane_rect.width() // 4
        rel_y = canvas_top_offset + 110
        cx_t = pane_rect.left + rel_x
        cy_t = pane_rect.top + rel_y

        try:
            win.set_focus()
            time.sleep(0.3)
            from pywinauto.mouse import right_click
            right_click(coords=(cx_t, cy_t))
        except Exception as e:
            print(f"  [WARN] right_click 실패: {e}")

        time.sleep(1.0)
        # 컨텍스트 메뉴 후보 수집 — main window children의 unnamed Window도 popup 가능
        sources = []
        for w in app.windows():
            ct_w = w.element_info.control_type or ""
            n_w  = w.element_info.name or ""
            if "MultiTool Creator" in n_w or n_w == "Rad Menu":
                continue
            if ct_w in ("Menu", "Popup", "Window"):
                sources.append(w)
        try:
            top = app.top_window()
            for c in top.children():
                ct = c.element_info.control_type or ""
                n  = c.element_info.name or ""
                if ct == "Window" and not n:
                    sources.append(c)
        except Exception:
            pass

        seen_labels = set()
        for w in sources:
            try:
                mis = list(w.descendants(control_type="MenuItem"))
            except Exception:
                continue
            if not mis:
                continue
            for mi in mis:
                label = _get_label(mi)
                if not label or label in ("FILE", "PROJECT", "HELP") or label in seen_labels:
                    continue
                seen_labels.add(label)
                try:
                    r = mi.rectangle()
                    cx_m = (r.left + r.right) // 2
                    cy_m = (r.top + r.bottom) // 2
                except Exception:
                    cx_m = cy_m = 0
                items.append({
                    "name":          label,
                    "shortcut":      _parse_shortcut(mi.element_info.name),
                    "automation_id": mi.element_info.automation_id,
                    "coordinates":   [cx_m, cy_m]
                })
            if items:
                break
        if not items:
            print(f"  [WARN] {target} 컨텍스트 메뉴 수집 0개 (좌표 {cx_t},{cy_t})")
    except Exception as e:
        print(f"  [WARN] {target} 우클릭 실패: {e}")
    finally:
        keyboard.send_keys("{ESC}")
        time.sleep(0.3)
    return items


# ── 공통 유틸 ─────────────────────────────────────────────────────────────────
def _get_label(elem) -> str:
    name = elem.element_info.name or ""
    if name and not name.startswith("MultiTool."):
        return name.split("\t")[0].strip()
    try:
        for child in elem.children(control_type="Text"):
            t = child.element_info.name.strip()
            if t:
                return t
    except Exception:
        pass
    return ""


def _parse_shortcut(text: str) -> str:
    parts = text.split("\t")
    return parts[1].strip() if len(parts) > 1 else ""
