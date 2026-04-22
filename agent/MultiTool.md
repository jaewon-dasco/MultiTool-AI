# EPEC MultiTool Agent 가이드

## 환경 정보

| 항목                 | 경로 / 값                                                          |
| -------------------- | ------------------------------------------------------------------ |
| MultiTool 실행파일   | `C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe`  |
| CoDeSys 2.3 실행파일 | `C:\Program Files (x86)\3S Software\CoDeSys V2.3\Codesys.exe`      |
| Python               | `C:\Users\JONE\AppData\Local\Programs\Python\Python313\python.exe` |
| 자동화 라이브러리    | pywinauto (`backend='uia'`, 64-bit Python에서 동작)                |

---

## MultiTool 표준 워크플로우

| 단계 | 작업                     | 자동화 방법     |
| ---- | ------------------------ | --------------- |
| 1    | 디바이스 추가            | XML 직접 수정   |
| 2    | 네트워크 추가            | XML 직접 수정   |
| 3    | 네트워크 연결            | XML 직접 수정   |
| 4    | CAN 설정                 | XML 직접 수정   |
| 5    | Diagnostics 설정         | XML 직접 수정   |
| 6    | OD 설정                  | XML 직접 수정   |
| 7    | PDO 설정                 | XML 직접 수정   |
| 8    | IO 설정                  | XML 직접 수정   |
| 9    | .exp 생성 (`Ctrl+Alt+E`) | pywinauto       |
| 10   | CoDeSys 임포트           | pywinauto / CLI |

---

## 단계별 XML 매핑

### 1. 디바이스 추가 — `<MachineType><Devices>`

```xml
<Device Guid="NEW-GUID">
  <DeviceTemplate>3606_21.xtmpl</DeviceTemplate>
</Device>
```

연동 필요: `<NetworkMappings>`, `<ProcessDataObjectMappings>`, `<NetworkEditor><EditorNodes>`, `<Device Guid="...">` 블록  
Device Template: `3606_01`, `3606_21`, `3606_22`, `3606_23`, `3606_24`, `3610_01`, `2040_Default` 등

---

### 2. 네트워크 추가 — `<MachineType><Networks>`

```xml
<Network Guid="NEW-GUID"><Name>NETWORK2</Name><Bitrate>250</Bitrate></Network>
```

---

### 3. 네트워크 연결 — `<MachineType><NetworkMappings>`

```xml
<Network Guid="NETWORK-GUID"><CAN Guid="DEVICE-CAN-GUID" /></Network>
```

---

### 4. CAN 설정 — `<Device><CANs><CAN><Settings>`

| XML 요소                 | 설명               | 예시값   |
| ------------------------ | ------------------ | -------- |
| `<CANNumber>`            | CAN 채널 번호      | `1`      |
| `<BitRate>`              | 통신 속도 (kbps)   | `250`    |
| `<NodeId>`               | CANopen 노드 ID    | `1`      |
| `<HeartbeatInterval>`    | 하트비트 주기 (ms) | `200`    |
| `<NmtProtocol>`          | NMT 역할           | `Master` |
| `<SyncCycleTime>`        | SYNC 주기 (ms)     | `200`    |
| `<SyncProducer>`         | SYNC 생산자 여부   | `False`  |
| `<DeviceProfile>`        | 디바이스 프로파일  | `405`    |
| `<ConfigurationTimeout>` | 설정 타임아웃 (ms) | `100`    |

---

### 5. Diagnostics — `<Device><CANs><CAN>`

```xml
<IODiagnosticSystem>
  <IsConsumer>false</IsConsumer>
  <IsProducer>false</IsProducer>
  <ProducerSourceID>0</ProducerSourceID>
</IODiagnosticSystem>
```

---

### 6. OD 설정 — `<Device><CANs><CAN><Parameters><ObjectDictionary>`

```xml
<ObjectDictionaryIndex Guid="NEW-GUID" IsEditable="true" IsAuto="false">
  <Name>MyParam</Name>
  <Index>2203</Index>
  <DataType>BYTE</DataType>
  <VariableType>Parameter</VariableType>
  <IndexType>Record</IndexType>
  <ObjectDictionarySubIndexes>
    <ObjectDictionarySubIndex Guid="NEW-GUID">
      <Name>Value1</Name><Index>1</Index><DataType>UINT</DataType>
      <AccessType>RW</AccessType><PdoMappable>false</PdoMappable>
      <ObjectDictionaryValue><Default>100</Default><Minimum>0</Minimum><Maximum>1000</Maximum></ObjectDictionaryValue>
    </ObjectDictionarySubIndex>
  </ObjectDictionarySubIndexes>
</ObjectDictionaryIndex>
```

**주의**: `<Editor><Networks><Network><Data>` 파라미터 그룹과 SyncGuid 양방향 동기화 필요.

---

### 7. PDO 설정 — `<Device><CANs><CAN><Parameters><ProcessDataObjects>`

```xml
<TransferProcessDataObject Guid="NEW-GUID">
  <Name>TPDO3</Name><CobId>381</CobId><CobIdType>Default</CobIdType>
  <DataLengthCode>8</DataLengthCode><EventTimer>300</EventTimer>
  <InhibitTime>100</InhibitTime><TransmissionType>Async</TransmissionType>
</TransferProcessDataObject>

<ReceiveProcessDataObject Guid="NEW-GUID">
  <Name>RPDO2</Name><CobId>300</CobId><CobIdType>Manual</CobIdType>
  <DataLengthCode>8</DataLengthCode>
</ReceiveProcessDataObject>
```

---

### 8. IO 설정 — `<Device><IO><Connectors><Connector><Pins>`

```xml
<Pin Guid="PIN-GUID" IsReadOnly="false">
  <Id>20</Id><Variable>MY_SENSOR</Variable><SelectedModes>7</SelectedModes>
  <Variables>
    <RefVariable Modes="7">
      <Variable><Name>aiX1_20_FilterSize</Name><Value>10</Value></Variable>
    </RefVariable>
  </Variables>
</Pin>
```

**핀 모드 실측값:**

| 값   | 모드 | 설명                                        | 예시 핀                |
| ---- | ---- | ------------------------------------------- | ---------------------- |
| `2`  | DI   | 디지털 입력                                 | 14(SW_FOOT)            |
| `3`  | DO   | 디지털 출력                                 | 7(LED1)                |
| `4`  | PWM  | PWM 출력                                    | 2(VAVLE_UP)            |
| `7`  | FB   | 필터링 아날로그 입력 (`G_AIBufferOf_` 생성) | 20(JOYSTICK_MV)        |
| `22` | PI   | 비례적분 제어 (밸브 전류 피드백)            | 22(VALVE_UPDN_CURRENT) |

---

## 단계 9~10: .exp 생성 및 CoDeSys 전달

| 항목               | 값                                                |
| ------------------ | ------------------------------------------------- |
| System Export 출력 | `CU_3606_21_generated.exp` (NOT `CU_3606_21.exp`) |
| 단축키             | `Ctrl+Alt+E` (MultiTool 포커스 필수)              |
| 메뉴 경로          | PROJECT → System Export                           |

### 방법 A — Ctrl+Alt+E (권장)

```python
import ctypes, time, win32gui, win32con
from pywinauto import Application
from pywinauto.keyboard import send_keys

def focus_and_export():
    found = []
    win32gui.EnumWindows(lambda h, _: found.append(h)
        if 'MultiTool' in win32gui.GetWindowText(h) and win32gui.IsWindowVisible(h) else None, None)
    if found:
        win32gui.ShowWindow(found[0], win32con.SW_RESTORE)
        ctypes.windll.user32.SwitchToThisWindow(found[0], True)  # SetForegroundWindow 대신 사용
        time.sleep(0.5)
    app = Application(backend='uia').connect(title_re='.*MultiTool.*', timeout=8)
    app.top_window().set_focus()
    time.sleep(0.3)
    send_keys('^%e')   # Ctrl+Alt+E
    time.sleep(5)      # _generated.exp 갱신 대기
```

### 방법 B — PROJECT 메뉴 클릭 (Ctrl+Alt+E 무반응 시)

```python
menu = win.child_window(title='Rad Menu', control_type='Menu')
win.child_window(title='Rad Menu', control_type='Menu').children(control_type='MenuItem')[1].click_input()
time.sleep(0.8)
for d in win.descendants(control_type='MenuItem'):
    children = d.children(control_type='Text')
    if 'System Export' in (children[0].window_text() if children else d.window_text()):
        d.click_input(); break
```

### 방법 C — CoDeSys script.dat 자동 임포트

```python
subprocess.Popen([CODESYS, '/cmd', 'script.dat'],
    cwd=r'C:\Users\JONE\Desktop\EPEC\CoDeSysProject\DasDemoProject\CU_3606_21')
```

---

## pywinauto UI 탐색 결과 (실측)

```python
app = Application(backend='uia').connect(title_re='.*MultiTool.*', timeout=8)
win = app.top_window()
```

### 주요 auto_id

| auto_id                              | 역할                      |
| ------------------------------------ | ------------------------- |
| `MainView_MultiToolMainWindow`       | 메인 윈도우               |
| `MainView_NetworkEditorView`         | 네트워크 에디터 우측 패널 |
| `NetworkEditorView_AddDeviceButton`  | 디바이스 추가 버튼        |
| `NetworkEditorView_AddNetworkButton` | 네트워크 추가 버튼        |
| `radDocking`                         | 도킹 레이아웃 (Telerik)   |
| `IsBusyIndicator`                    | 로딩 Progress Bar         |
| `ComboBoxSelectedMachinetype`        | Machine Type 콤보박스     |

### 메뉴 구조

```
Rad Menu → [0] FILE  [1] PROJECT  [2] HELP
```

**주의**: `MenuItem.window_text()` = ViewModel 이름; 실제 텍스트는 `MenuItem.children(control_type='Text')[0].window_text()`

---

## XML 루트 구조 (실측)

```
MtProject
├── Meta
├── Project/MachineType  ← GUID 참조 (Devices/Networks/NetworkMappings)
├── NetworkEditors
├── Editor
└── Device Guid="..."    ← 실제 장치 데이터 (MtProject 최상위)
    ├── CANs/CAN/Settings
    ├── CANs/CAN/Parameters/ObjectDictionary
    ├── CANs/CAN/Parameters/ProcessDataObjects
    ├── CANs/CAN/IODiagnosticSystem
    └── IO/Connectors/Connector/Pins/Pin
```

### IO Connector/Pin Python 탐색

```python
for conn in dev.find('IO').findall('.//Connector'):
    cid = conn.find('Id').text          # Id는 자식 요소 (attribute 아님)
    for pin in conn.find('Pins').findall('Pin'):
        pid = pin.findtext('Id')
        var = pin.findtext('Variable', '')
        mode = pin.findtext('SelectedModes', '')
```

---

## GUID 생성 / SyncGuid

```python
import uuid
new_guid = str(uuid.uuid4())
```

OD SubIndex는 `<Parameters>` + `<Editor>` 양쪽에 같은 SyncGuid로 연결 — 둘 다 설정 필요.

---

## 트러블슈팅

| 증상                   | 원인                  | 조치                                 |
| ---------------------- | --------------------- | ------------------------------------ |
| MultiTool 로드 실패    | GUID 불일치           | 4개 섹션 GUID 교차 검증              |
| .exp 생성 후 내용 없음 | SyncGuid 누락         | Editor/Parameters 양쪽 SyncGuid 확인 |
| CoDeSys import 오류    | .exp 형식 오류        | MultiTool System Export 재실행       |
| Ctrl+Alt+E 무반응      | MultiTool 포커스 없음 | `SwitchToThisWindow` 후 재시도       |
