# -*- coding: utf-8 -*-
"""
EPEC MultiTool .mtproject XML 자동화 편집기
사용 전 MultiTool을 자동으로 종료하고, 편집 후 재실행합니다.
"""
import uuid
import subprocess
import sys
import time
from pathlib import Path
from xml.etree import ElementTree as ET

# ── 경로 설정 ──────────────────────────────────────────────────────────────────
MULTITOOL_EXE = r"C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe"
MTPROJECT_PATH = Path(r"C:\Users\JONE\Desktop\EPEC\CoDeSysProject\DasDemoProject\DasDemoProject.mtproject")
LOCKFILE = MTPROJECT_PATH.parent / "~$projlock.mtproject"

ET.register_namespace('', '')


# ── 유틸 ───────────────────────────────────────────────────────────────────────
def new_guid():
    return str(uuid.uuid4())


def close_multitool():
    """MultiTool 프로세스 종료 및 잠금 파일 해제 대기"""
    result = subprocess.run(
        ['taskkill', '/F', '/IM', 'MultiTool.exe'],
        capture_output=True
    )
    if result.returncode == 0:
        print("MultiTool 종료됨")
        for _ in range(20):
            if not LOCKFILE.exists():
                break
            time.sleep(0.5)
    else:
        print("MultiTool 실행 중 아님")


def open_multitool():
    """편집 완료 후 MultiTool 재실행"""
    subprocess.Popen([MULTITOOL_EXE, str(MTPROJECT_PATH)])
    print(f"MultiTool 재실행: {MTPROJECT_PATH.name}")


def load(path=MTPROJECT_PATH):
    tree = ET.parse(path)
    return tree, tree.getroot()


def save(tree, path=MTPROJECT_PATH):
    ET.indent(tree, space='  ')
    tree.write(path, encoding='utf-8', xml_declaration=True)
    print(f"저장 완료: {path}")


def _machine_type(root):
    return root.find('.//MachineType')


# ── 1. Device 추가 ─────────────────────────────────────────────────────────────
def add_device(root, template='3606_21.xtmpl'):
    """
    Device를 추가하고 생성된 GUID를 반환.
    NetworkMappings/ProcessDataObjectMappings/NetworkEditor 연결은 별도 호출 필요.
    """
    mt = _machine_type(root)
    guid = new_guid()
    dev = ET.SubElement(mt.find('Devices'), 'Device', Guid=guid)
    ET.SubElement(dev, 'DeviceTemplate').text = template
    print(f"Device 추가: {template} (GUID={guid})")
    return guid


# ── 2. Network 추가 ────────────────────────────────────────────────────────────
def add_network(root, name='NETWORK2', bitrate=250):
    mt = _machine_type(root)
    guid = new_guid()
    net = ET.SubElement(mt.find('Networks'), 'Network', Guid=guid)
    ET.SubElement(net, 'Name').text = name
    ET.SubElement(net, 'Bitrate').text = str(bitrate)
    print(f"Network 추가: {name} {bitrate}kbps (GUID={guid})")
    return guid


# ── 3. Network-CAN 연결 ────────────────────────────────────────────────────────
def map_network_to_can(root, network_guid, can_guid):
    """NetworkMappings에 네트워크-CAN 연결 추가"""
    mt = _machine_type(root)
    mappings = mt.find('NetworkMappings')
    net_el = ET.SubElement(mappings, 'Network', Guid=network_guid)
    ET.SubElement(net_el, 'CAN', Guid=can_guid)
    print(f"NetworkMapping: Network={network_guid[:8]}… → CAN={can_guid[:8]}…")


# ── 4. CAN 설정 조회/수정 ──────────────────────────────────────────────────────
def get_can(root, device_guid, can_number=1):
    """device_guid 디바이스의 CAN 채널 Element 반환"""
    for can in root.findall(f'.//Device[@Guid="{device_guid}"]//CAN'):
        num = can.find('Settings/CANNumber')
        if num is not None and num.text == str(can_number):
            return can
    return None


def set_can_settings(root, device_guid, can_number=1, **kwargs):
    """
    CAN 설정 수정. kwargs 예:
      BitRate=250, NodeId=1, HeartbeatInterval=200,
      NmtProtocol='Master', SyncCycleTime=200
    """
    can = get_can(root, device_guid, can_number)
    if can is None:
        print(f"CAN{can_number} 없음 (Device={device_guid[:8]}…)")
        return
    settings = can.find('Settings')
    for key, val in kwargs.items():
        el = settings.find(key)
        if el is not None:
            el.text = str(val)
            print(f"  CAN{can_number}.{key} = {val}")


# ── 5. IO 핀 설정 ──────────────────────────────────────────────────────────────
def set_io_pin(root, device_guid, connector_id, pin_id, variable, mode, filter_size=None):
    """
    IO 핀 설정 (변수명, 모드).
    mode: 2=DI, 3=DO, 4=PWM, 5=AI
    """
    dev_el = root.find(f'.//Device[@Guid="{device_guid}"]')
    if dev_el is None:
        print(f"Device {device_guid[:8]}… 없음")
        return
    for pin in dev_el.findall(f'.//Connector[@Id="{connector_id}"]//Pin'):
        if pin.find('Id') is not None and pin.find('Id').text == str(pin_id):
            _set_or_create(pin, 'Variable', variable)
            _set_or_create(pin, 'SelectedModes', str(mode))
            if filter_size is not None and mode == 5:
                _ensure_ai_filter(pin, filter_size)
            print(f"  Pin {connector_id}.{pin_id}: {variable} mode={mode}")
            return
    print(f"Pin {connector_id}.{pin_id} 없음")


def _set_or_create(parent, tag, text):
    el = parent.find(tag)
    if el is None:
        el = ET.SubElement(parent, tag)
    el.text = text


def _ensure_ai_filter(pin, size):
    for rv in pin.findall('.//RefVariable[@Modes="5"]//Variable'):
        if rv.find('Name') is not None and rv.find('Name').text.startswith('aiX'):
            rv.find('Value').text = str(size)
            return


# ── 6. OD 파라미터 추가 ────────────────────────────────────────────────────────
def add_od_parameter(root, device_guid, can_number=1,
                     name='NewParam', index=0x2203, data_type='BYTE',
                     subindexes=None):
    """
    OD Record 파라미터 추가.
    subindexes: [{'name': 'Val', 'index': 1, 'data_type': 'UINT',
                  'access': 'RW', 'default': 0, 'min': 0, 'max': 1000}]
    """
    can = get_can(root, device_guid, can_number)
    if can is None:
        return
    od = can.find('.//ObjectDictionary')
    if od is None:
        od = ET.SubElement(can.find('Parameters'), 'ObjectDictionary')

    idx_guid = new_guid()
    idx_el = ET.SubElement(od, 'ObjectDictionaryIndex',
                            Guid=idx_guid, IsEditable='true', IsAuto='false')
    ET.SubElement(idx_el, 'Name').text = name
    ET.SubElement(idx_el, 'Index').text = str(index)
    ET.SubElement(idx_el, 'DataType').text = data_type
    ET.SubElement(idx_el, 'VariableType').text = 'Parameter'
    ET.SubElement(idx_el, 'IndexType').text = 'Record'
    subs_el = ET.SubElement(idx_el, 'ObjectDictionarySubIndexes')

    sync_guids = []
    for sub in (subindexes or []):
        sg = new_guid()
        sync_guids.append(sg)
        sub_el = ET.SubElement(subs_el, 'ObjectDictionarySubIndex', Guid=sg)
        ET.SubElement(sub_el, 'Name').text = sub['name']
        ET.SubElement(sub_el, 'Index').text = str(sub['index'])
        ET.SubElement(sub_el, 'DataType').text = sub.get('data_type', 'UINT')
        ET.SubElement(sub_el, 'AccessType').text = sub.get('access', 'RW')
        ET.SubElement(sub_el, 'PdoMappable').text = 'false'
        val_el = ET.SubElement(sub_el, 'ObjectDictionaryValue')
        ET.SubElement(val_el, 'Default').text = str(sub.get('default', 0))
        ET.SubElement(val_el, 'Minimum').text = str(sub.get('min', 0))
        ET.SubElement(val_el, 'Maximum').text = str(sub.get('max', 1000))

    print(f"OD 추가: {name} 0x{index:04X} ({len(subindexes or [])} subindex)")
    return idx_guid, sync_guids


# ── 7. PDO 추가 ───────────────────────────────────────────────────────────────
def add_tpdo(root, device_guid, can_number=1,
             name='TPDO3', cob_id=0x381, dlc=8, event_timer=300):
    can = get_can(root, device_guid, can_number)
    if can is None:
        return
    pdos = can.find('.//ProcessDataObjects')
    if pdos is None:
        pdos = ET.SubElement(can.find('Parameters'), 'ProcessDataObjects')
    guid = new_guid()
    tpdo = ET.SubElement(pdos, 'TransferProcessDataObject', Guid=guid)
    ET.SubElement(tpdo, 'Name').text = name
    ET.SubElement(tpdo, 'CobId').text = str(cob_id)
    ET.SubElement(tpdo, 'CobIdType').text = 'Manual'
    ET.SubElement(tpdo, 'DataLengthCode').text = str(dlc)
    ET.SubElement(tpdo, 'EventTimer').text = str(event_timer)
    ET.SubElement(tpdo, 'TransmissionType').text = 'Async'
    print(f"TPDO 추가: {name} COB-ID=0x{cob_id:03X}")
    return guid


def add_rpdo(root, device_guid, can_number=1,
             name='RPDO2', cob_id=0x300, dlc=8):
    can = get_can(root, device_guid, can_number)
    if can is None:
        return
    pdos = can.find('.//ProcessDataObjects')
    if pdos is None:
        pdos = ET.SubElement(can.find('Parameters'), 'ProcessDataObjects')
    guid = new_guid()
    rpdo = ET.SubElement(pdos, 'ReceiveProcessDataObject', Guid=guid)
    ET.SubElement(rpdo, 'Name').text = name
    ET.SubElement(rpdo, 'CobId').text = str(cob_id)
    ET.SubElement(rpdo, 'CobIdType').text = 'Manual'
    ET.SubElement(rpdo, 'DataLengthCode').text = str(dlc)
    print(f"RPDO 추가: {name} COB-ID=0x{cob_id:03X}")
    return guid


# ── 메인 예시 ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # 1. MultiTool 종료
    close_multitool()

    # 2. XML 로드
    tree, root = load()

    # ── 여기서부터 원하는 수정 작업 ──
    # 예: CAN1 설정 변경
    device_guid = '57f1a44d-ba6e-4a58-95b3-cb1956c242e2'  # 현재 프로젝트 Device GUID

    set_can_settings(root, device_guid, can_number=1,
                     BitRate=250, HeartbeatInterval=200)

    # 예: OD 파라미터 추가
    # add_od_parameter(root, device_guid, index=0x2203, name='Regulation',
    #     subindexes=[
    #         {'name': 'TargetAngle', 'index': 1, 'data_type': 'INT',
    #          'default': 0, 'min': -1800, 'max': 1800},
    #     ])

    # 3. 저장
    save(tree)

    # 4. MultiTool 재실행
    open_multitool()
