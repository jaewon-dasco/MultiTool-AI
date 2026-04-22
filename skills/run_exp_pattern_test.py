# -*- coding: utf-8 -*-
"""
MultiTool .exp 패턴 분석 순차 테스트
각 변경 후 .exp diff를 캡처해 docs/exp_diffs/ 에 저장한다.

실행:
  py skills/run_exp_pattern_test.py              # 전체
  py skills/run_exp_pattern_test.py --step 3    # 단일 단계
"""
import argparse
import difflib
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from xml.etree import ElementTree as ET

import win32api
import win32con
import win32gui
from pywinauto import Application
from pywinauto.keyboard import send_keys

# ── 경로 ────────────────────────────────────────────────────────────────────────
BASE        = Path(r'C:\Users\JONE\Desktop\EPEC\CoDeSysProject')
MT_EXE      = r'C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe'
MT_PROJECT  = BASE / 'DasDemoProject' / 'DasDemoProject.mtproject'
LOCKFILE    = MT_PROJECT.parent / '~$projlock.mtproject'
EXP_PATH    = BASE / 'DasDemoProject' / 'CU_3606_21' / 'CU_3606_21.exp'
DIFF_DIR    = BASE / 'docs' / 'exp_diffs'
DIFF_DIR.mkdir(parents=True, exist_ok=True)

DEV_GUID    = '57f1a44d-ba6e-4a58-95b3-cb1956c242e2'
NET_GUID    = '50de4331-ddb3-4edf-b347-444faa7160b4'

ET.register_namespace('', '')


# ── 유틸 ────────────────────────────────────────────────────────────────────────
def new_guid(): return str(uuid.uuid4())

def load():
    tree = ET.parse(MT_PROJECT)
    return tree, tree.getroot()

def save(tree):
    ET.indent(tree, space='  ')
    tree.write(MT_PROJECT, encoding='utf-8', xml_declaration=True)

def close_multitool():
    r = subprocess.run(['taskkill', '/F', '/IM', 'MultiTool.exe'], capture_output=True)
    if r.returncode == 0:
        for _ in range(20):
            if not LOCKFILE.exists(): break
            time.sleep(0.5)

def open_multitool(wait=7):
    subprocess.Popen([MT_EXE, str(MT_PROJECT)])
    time.sleep(wait)

def multitool_hwnd():
    found = []
    def cb(h, _):
        if 'MultiTool' in win32gui.GetWindowText(h) and win32gui.IsWindowVisible(h):
            found.append(h)
    win32gui.EnumWindows(cb, None)
    return found[0] if found else None

def focus_multitool():
    hwnd = multitool_hwnd()
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        try:
            # SetForegroundWindow는 다른 프로세스가 포커스를 가질 때 실패할 수 있음
            # AllowSetForegroundWindow 없이 강제 포커스
            win32gui.BringWindowToTop(hwnd)
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
            except Exception:
                pass
        time.sleep(0.4)

def generate_exp():
    """PROJECT 메뉴 → System Export → .exp 생성. 타임아웃 30초."""
    mtime_before = EXP_PATH.stat().st_mtime if EXP_PATH.exists() else 0

    try:
        app = Application(backend='uia').connect(title_re='.*MultiTool.*', timeout=8)
        win = app.top_window()

        # 1. 포커스
        hwnd = multitool_hwnd()
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            try:
                import ctypes
                ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
            except Exception:
                pass
        time.sleep(0.5)
        win.set_focus()
        time.sleep(0.3)

        # 2. 방법A: Ctrl+Alt+E 먼저 시도
        send_keys('^%e')
        print("  Ctrl+Alt+E 전송")
        time.sleep(3)

        # .exp 갱신 확인
        if EXP_PATH.exists() and EXP_PATH.stat().st_mtime > mtime_before:
            return True

        # 3. 방법B: PROJECT 메뉴 → System Export 클릭
        print("  Ctrl+Alt+E 무반응 → PROJECT 메뉴 클릭 시도")
        menu = win.child_window(title="Rad Menu", control_type="Menu")
        proj_items = menu.children(control_type="MenuItem")
        if len(proj_items) > 1:
            proj_items[1].click_input()   # PROJECT
            time.sleep(0.8)
            # System Export MenuItem 탐색
            for d in win.descendants(control_type="MenuItem"):
                txt = d.window_text()
                child_statics = d.children(control_type="Text")
                label = child_statics[0].window_text() if child_statics else txt
                if 'export' in label.lower() or 'system' in label.lower() or 'Export' in label:
                    print(f"  클릭: '{label}'")
                    d.click_input()
                    break
            else:
                # 못 찾으면 전체 MenuItem 출력 후 ESC
                print("  System Export 못 찾음. 메뉴 항목:")
                for d in win.descendants(control_type="MenuItem"):
                    children = d.children(control_type="Text")
                    label = children[0].window_text() if children else d.window_text()
                    print(f"    '{label}'")
                send_keys('{ESC}')

    except Exception as e:
        print(f"  UIA 오류: {e}")
        # 최후 수단: 직접 키 전송
        win32api.keybd_event(0x11, 0, 0, 0)
        win32api.keybd_event(0x12, 0, 0, 0)
        win32api.keybd_event(0x45, 0, 0, 0)
        time.sleep(0.1)
        win32api.keybd_event(0x45, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x12, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)

    # .exp 파일 갱신 대기 (최대 30초)
    for _ in range(60):
        time.sleep(0.5)
        if EXP_PATH.exists() and EXP_PATH.stat().st_mtime > mtime_before:
            return True
    return False

def capture_diff(before: Path, step_name: str):
    """before vs 현재 .exp diff를 파일에 저장."""
    if not before.exists() or not EXP_PATH.exists():
        print(f"  [!] diff 불가 (파일 없음)")
        return
    a = before.read_text(encoding='utf-8', errors='replace').splitlines()
    b = EXP_PATH.read_text(encoding='utf-8', errors='replace').splitlines()
    diff = list(difflib.unified_diff(a, b, fromfile='before.exp', tofile='after.exp',
                                     lineterm='', n=3))
    out = DIFF_DIR / f'{step_name}.diff'
    out.write_text('\n'.join(diff), encoding='utf-8')
    added   = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
    removed = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))
    print(f"  diff 저장: {out.name}  (+{added} / -{removed} 줄)")

def run_step(name: str, apply_fn, revert_fn=None):
    """
    단계 실행:
      1. 현재 .exp 백업
      2. XML 수정
      3. MultiTool 재시작 → exp 생성
      4. diff 캡처
      5. revert (있으면)
    """
    print(f"\n{'='*60}")
    print(f"STEP: {name}")
    print('='*60)

    # 백업
    before = DIFF_DIR / f'{name}_before.exp'
    if EXP_PATH.exists():
        shutil.copy2(EXP_PATH, before)
        print(f"  .exp 백업 완료")

    # MultiTool 종료 → XML 수정 → 재시작
    close_multitool()
    apply_fn()
    save_tree_global()
    open_multitool(wait=7)

    # exp 생성
    ok = generate_exp()
    if ok:
        print(f"  .exp 생성 완료")
        capture_diff(before, name)
    else:
        print(f"  [!] .exp 생성 실패 (timeout) - Ctrl+Alt+E 확인 필요")

    # 원복
    if revert_fn:
        close_multitool()
        revert_fn()
        save_tree_global()
        open_multitool(wait=5)


# ── 전역 tree 관리 ────────────────────────────────────────────────────────────
_tree = None
_root = None

def load_tree():
    global _tree, _root
    _tree, _root = load()

def save_tree_global():
    save(_tree)

def dev():  return _root.find('Device')
def mt():   return _root.find('.//MachineType')
def get_can():
    for can in dev().findall('.//CAN'):
        if can.findtext('Settings/NodeId') is not None:
            return can
    return dev().find('.//CAN')


# ── 각 단계 변경 함수 ─────────────────────────────────────────────────────────

# Step 1: Device 추가
_added_dev_guid = None
def step1_add_device():
    global _added_dev_guid
    load_tree()
    _added_dev_guid = new_guid()
    devices_el = mt().find('Devices')
    ET.SubElement(devices_el, 'Device', Guid=_added_dev_guid)
    # 새 Device 요소 최상위에 추가
    new_dev = ET.SubElement(_root, 'Device', Guid=_added_dev_guid)
    ET.SubElement(new_dev, 'Name').text = 'TestDevice2'
    ET.SubElement(new_dev, 'Attributes').text = ''
    tmpl = ET.SubElement(new_dev, 'Attributes')
    ET.SubElement(new_dev, 'DeviceTemplate').text = '3606_21.xtmpl'
    print(f"  Device 추가: GUID={_added_dev_guid[:8]}...")

def step1_revert():
    load_tree()
    # MachineType/Devices에서 제거
    devices_el = mt().find('Devices')
    for d in devices_el.findall('Device'):
        if d.get('Guid') == _added_dev_guid:
            devices_el.remove(d)
    # 최상위 Device 제거
    for d in _root.findall('Device'):
        if d.get('Guid') == _added_dev_guid:
            _root.remove(d)
    print(f"  Device 제거 (원복)")


# Step 2: Network 추가
_added_net_guid = None
def step2_add_network():
    global _added_net_guid
    load_tree()
    _added_net_guid = new_guid()
    networks_el = mt().find('Networks')
    net = ET.SubElement(networks_el, 'Network', Guid=_added_net_guid)
    ET.SubElement(net, 'Name').text = 'NETWORK2'
    ET.SubElement(net, 'Bitrate').text = '500'
    print(f"  Network 추가: NETWORK2 500kbps GUID={_added_net_guid[:8]}...")

def step2_revert():
    load_tree()
    networks_el = mt().find('Networks')
    for n in networks_el.findall('Network'):
        if n.get('Guid') == _added_net_guid:
            networks_el.remove(n)


# Step 3: CAN 설정 변경
def step3_can_settings():
    load_tree()
    can = get_can()
    s = can.find('Settings')
    _set(s, 'NodeId', '2')
    _set(s, 'HeartbeatInterval', '300')
    _set(s, 'SyncCycleTime', '100')
    print("  CAN: NodeId=2, HB=300, Sync=100")

def step3_revert():
    load_tree()
    can = get_can()
    s = can.find('Settings')
    _set(s, 'NodeId', '1')
    _set(s, 'HeartbeatInterval', '200')
    _set(s, 'SyncCycleTime', '200')


# Step 4: Diagnostic 설정
def step4_diagnostic():
    load_tree()
    diag = dev().find('.//IODiagnosticSystem')
    if diag is None:
        can = get_can()
        diag = ET.SubElement(can, 'IODiagnosticSystem')
    _set(diag, 'IsConsumer', 'true')
    _set(diag, 'IsProducer', 'true')
    _set(diag, 'ProducerSourceID', '1')
    print("  Diagnostic: IsConsumer=true, IsProducer=true, SourceID=1")

def step4_revert():
    load_tree()
    diag = dev().find('.//IODiagnosticSystem')
    if diag is not None:
        _set(diag, 'IsConsumer', 'false')
        _set(diag, 'IsProducer', 'false')
        _set(diag, 'ProducerSourceID', '0')


# Step 5: OD 추가 (새 파라미터 0x2203)
_added_od_guid = None
def step5_od_add():
    global _added_od_guid
    load_tree()
    od = dev().find('.//ObjectDictionary')
    _added_od_guid = new_guid()
    idx = ET.SubElement(od, 'ObjectDictionaryIndex',
                        Guid=_added_od_guid, IsEditable='true', IsAuto='false')
    ET.SubElement(idx, 'Name').text = 'TestParam'
    ET.SubElement(idx, 'Index').text = '8707'   # 0x2203
    ET.SubElement(idx, 'DataType').text = 'BYTE'
    ET.SubElement(idx, 'VariableType').text = 'Parameter'
    ET.SubElement(idx, 'IndexType').text = 'Record'
    subs = ET.SubElement(idx, 'ObjectDictionarySubIndexes')
    sg = new_guid()
    sub = ET.SubElement(subs, 'ObjectDictionarySubIndex', Guid=sg)
    ET.SubElement(sub, 'Name').text = 'Value1'
    ET.SubElement(sub, 'Index').text = '1'
    ET.SubElement(sub, 'DataType').text = 'UINT'
    ET.SubElement(sub, 'AccessType').text = 'RW'
    ET.SubElement(sub, 'PdoMappable').text = 'false'
    val = ET.SubElement(sub, 'ObjectDictionaryValue')
    ET.SubElement(val, 'Default').text = '0'
    ET.SubElement(val, 'Minimum').text = '0'
    ET.SubElement(val, 'Maximum').text = '1000'
    print("  OD 추가: TestParam 0x2203")

def step5_revert():
    load_tree()
    od = dev().find('.//ObjectDictionary')
    for idx in od.findall('ObjectDictionaryIndex'):
        if idx.get('Guid') == _added_od_guid:
            od.remove(idx)
            break


# Step 6a: TPDO 추가
_added_tpdo_guid = None
def step6a_tpdo():
    global _added_tpdo_guid
    load_tree()
    pdos = dev().find('.//ProcessDataObjects')
    _added_tpdo_guid = new_guid()
    t = ET.SubElement(pdos, 'TransferProcessDataObject', Guid=_added_tpdo_guid)
    ET.SubElement(t, 'Name').text = 'TPDO3'
    ET.SubElement(t, 'CobId').text = '769'    # 0x301
    ET.SubElement(t, 'CobIdType').text = 'Manual'
    ET.SubElement(t, 'DataLengthCode').text = '8'
    ET.SubElement(t, 'EventTimer').text = '300'
    ET.SubElement(t, 'TransmissionType').text = 'Async'
    print("  TPDO3 추가: COB-ID=0x301")

def step6a_revert():
    load_tree()
    pdos = dev().find('.//ProcessDataObjects')
    for p in pdos.findall('TransferProcessDataObject'):
        if p.get('Guid') == _added_tpdo_guid:
            pdos.remove(p)
            break


# Step 6b: RPDO 추가
_added_rpdo_guid = None
def step6b_rpdo():
    global _added_rpdo_guid
    load_tree()
    pdos = dev().find('.//ProcessDataObjects')
    _added_rpdo_guid = new_guid()
    r = ET.SubElement(pdos, 'ReceiveProcessDataObject', Guid=_added_rpdo_guid)
    ET.SubElement(r, 'Name').text = 'RPDO2'
    ET.SubElement(r, 'CobId').text = '513'    # 0x201 + 0x100 = 0x301 → 0x300
    ET.SubElement(r, 'CobIdType').text = 'Manual'
    ET.SubElement(r, 'DataLengthCode').text = '8'
    print("  RPDO2 추가: COB-ID=0x201")

def step6b_revert():
    load_tree()
    pdos = dev().find('.//ProcessDataObjects')
    for p in pdos.findall('ReceiveProcessDataObject'):
        if p.get('Guid') == _added_rpdo_guid:
            pdos.remove(p)
            break


# Step 8: IO 핀 모드별 변경
def _set(parent, tag, text):
    el = parent.find(tag)
    if el is None:
        el = ET.SubElement(parent, tag)
    el.text = text

def _get_pin(connector_id_val, pin_id_val):
    """Connector/Pins/Pin 찾기 — Id 는 자식 요소, Pins 래퍼 있음"""
    io = dev().find('IO')
    for conn in io.findall('.//Connector'):
        cid_el = conn.find('Id')
        if cid_el is not None and cid_el.text == str(connector_id_val):
            pins_el = conn.find('Pins')
            target = pins_el if pins_el is not None else conn
            for pin in target.findall('Pin'):
                pid_el = pin.find('Id')
                if pid_el is not None and pid_el.text == str(pin_id_val):
                    return pin
    return None

def _pin_set(connector, pin_id, var, mode):
    """핀 Variable + SelectedModes 설정"""
    pin = _get_pin(connector, pin_id)
    if pin is None:
        print(f"  [!] Pin {connector}.{pin_id} 없음")
        return False
    _set(pin, 'Variable', var)
    _set(pin, 'SelectedModes', str(mode))
    print(f"  Pin {connector}.{pin_id}: {var} mode={mode}")
    return True

def _pin_clear(connector, pin_id, orig_var, orig_mode):
    """핀 원복"""
    pin = _get_pin(connector, pin_id)
    if pin is None: return
    _set(pin, 'Variable', orig_var)
    if orig_mode:
        _set(pin, 'SelectedModes', str(orig_mode))
    else:
        el = pin.find('SelectedModes')
        if el is not None: pin.remove(el)

# 사용 가능한 핀 확인용
def list_pins():
    load_tree()
    io = dev().find('IO')
    print("  [핀 목록]")
    for conn in io.findall('.//Connector'):
        cid_el = conn.find('Id')
        cid = cid_el.text if cid_el is not None else '?'
        pins_el = conn.find('Pins')
        target = pins_el if pins_el is not None else conn
        for pin in target.findall('Pin'):
            pid = pin.findtext('Id','?')
            var = pin.findtext('Variable','')
            mode = pin.findtext('SelectedModes','')
            print(f"    Conn={cid} Pin={pid} var={var!r} mode={mode}")


# Step 8: IO 핀 모드별 변경
# 미사용 핀(9~12)을 활용해 각 모드 테스트
# 현재 상태: Pin9=X1_9(없음), Pin10=X1_10(없음), Pin11=X1_11(없음), Pin12=X1_12(없음)

def _make_io_step(pin_id, var, mode, orig_var, orig_mode):
    def apply():
        load_tree()
        _pin_set(1, pin_id, var, mode)
    def revert():
        load_tree()
        _pin_clear(1, pin_id, orig_var, orig_mode)
    return apply, revert

# 8a: DI (mode=2)
step8a_apply, step8a_revert = _make_io_step(9,  'TEST_DI',  2, 'X1_9',  None)
# 8b: DO (mode=3)
step8b_apply, step8b_revert = _make_io_step(10, 'TEST_DO',  3, 'X1_10', None)
# 8c: PWM (mode=4)
step8c_apply, step8c_revert = _make_io_step(11, 'TEST_PWM', 4, 'X1_11', None)
# 8d: AI/FB (mode=7) — 기존 Pin20(JOYSTICK_MV)과 같은 모드
step8d_apply, step8d_revert = _make_io_step(12, 'TEST_FB',  7, 'X1_12', None)
# 8e: PI (mode=22) — 기존 Pin22(VALVE_UPDN_CURRENT)와 같은 모드, 빈 핀 없으면 Pin12 재사용
step8e_apply, step8e_revert = _make_io_step(12, 'TEST_PI', 22, 'X1_12', None)


# ── 단계 정의 ─────────────────────────────────────────────────────────────────
STEPS = {
    1:    ('step1_device_add',   step1_add_device,  step1_revert),
    2:    ('step2_network_add',  step2_add_network,  step2_revert),
    3:    ('step3_can_settings', step3_can_settings, step3_revert),
    4:    ('step4_diagnostic',   step4_diagnostic,   step4_revert),
    5:    ('step5_od_add',       step5_od_add,       step5_revert),
    '6a': ('step6a_tpdo_add',   step6a_tpdo,        step6a_revert),
    '6b': ('step6b_rpdo_add',   step6b_rpdo,        step6b_revert),
    '8a': ('step8a_io_di',      step8a_apply,       step8a_revert),
    '8b': ('step8b_io_do',      step8b_apply,       step8b_revert),
    '8c': ('step8c_io_pwm',     step8c_apply,       step8c_revert),
    '8d': ('step8d_io_fb',      step8d_apply,       step8d_revert),
    '8e': ('step8e_io_pi',      step8e_apply,       step8e_revert),
}


# ── 메인 ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', default='all', help='단계 번호 또는 all / pins')
    args = parser.parse_args()

    if args.step == 'pins':
        load_tree()
        list_pins()
        sys.exit(0)

    if args.step == 'all':
        targets = list(STEPS.keys())
    else:
        targets = [args.step if args.step in STEPS else int(args.step)]

    for key in targets:
        if key not in STEPS:
            print(f"단계 {key} 없음")
            continue
        name, apply_fn, revert_fn = STEPS[key]
        run_step(name, apply_fn, revert_fn)

    print("\n=== 완료 ===")
    print(f"diff 파일: {DIFF_DIR}")
