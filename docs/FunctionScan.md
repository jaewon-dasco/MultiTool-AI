# FunctionScan

## Clarify

| 항목        | 내용                                                          |
| ----------- | ------------------------------------------------------------- |
| 입력        | `*.mtproject` (XML), `Manual.chm` (설치 경로 참조)            |
| 출력        | 기능 목록 + UI 조작 시퀀스 (단축키, 메뉴 경로, 좌표)          |
| 자동화 대상 | System Export, Parameter CSV Export, Network 편집, OD 편집 등 |
| 제약        | MultiTool Creator GUI 기반 — COM/API 없음, UI Automation 사용 |

### 스캔 실행 시 버전 확인 (매 실행)

1. `C:\Program Files (x86)\Epec\` → `MultiTool Creator *` 폴더 열거 → 설치 버전 갱신
2. 각 버전 `Resources\Manual.chm` 존재 + MD5 해시 확인
3. `docs/versions/`에 없는 버전 → CHM 추출 + UIA 덤프 신규 생성
4. 기존 버전 → 해시 변경 시에만 재추출·재덤프

### 업데이트 감지 전략

1. CHM 재추출 → `git diff`로 변경 HTM 파악
2. UIA 메뉴 트리 덤프 → 이전 덤프와 diff → 좌표 변화 탐지
3. 변경 항목만 재매핑

---

## Context Gather

### 설치 버전 현황

설치 경로: `C:\Program Files (x86)\Epec\MultiTool Creator {버전}\`

| 버전 | CHM                             |
| ---- | ------------------------------- |
| 8.1  | 없음                            |
| 8.2  | 없음                            |
| 8.4  | `Resources\Manual.chm` (6.3 MB) |

### 문서 버전 히스토리 (최신→과거)

| 날짜       | 버전         | 주요 변경                                |
| ---------- | ------------ | ---------------------------------------- |
| 2025-09-03 | **8.4** 최신 | System Requirements, Functional Versions |
| 2025-06-30 | 8.4          | System Requirements, Functional Versions |
| 2025-04-24 | 8.3          | Using Diagnostics, System Requirements   |
| 2025-02-18 | 8.2          | System Requirements, Library Manager     |
| 2024-11-25 | 8.1          | Slave Devices, PDOs, DBC Export/Import   |
| 2024-06-18 | 8.0          | Using Machine Types (신규)               |
| 2024-04-03 | 7.9          | Adding/Editing/Deleting Devices          |
| 2024-02-21 | 7.8          | CANopen Slave, System Requirements       |

### 버전별 덤프 구조

```
docs/versions/{버전}/
  meta.json          ← SDK/Tool 버전, CHM MD5, 덤프 날짜
  Manual_MultiTool.chm
  Manual_Libraries.chm
  chm_extracted/     ← HTM 추출본
  ui_tree/
    ui_tree_{timestamp}.json
  function_map.json
```

버전 번호: `.mtproject` `<SDK>` 태그 (`8.4.9308.1081` → `8.4`)

### `.mtproject` XML 구조

| 노드                          | 내용                                |
| ----------------------------- | ----------------------------------- |
| `<Meta>`                      | 생성/수정일, SDK, Tool 버전, 사용자 |
| `<Preferences>`               | EventLevels, OD 설정, ProjectKey    |
| `<MachineType>`               | 이름, GUID                          |
| `<Networks>`                  | 네트워크 목록 (이름, Bitrate)       |
| `<Devices>`                   | 디바이스 목록 (DeviceTemplate)      |
| `<NetworkMappings>`           | 네트워크↔CAN 채널 매핑              |
| `<ProcessDataObjectMappings>` | TPDO/RPDO 매핑 (서브인덱스 포함)    |

### 프로젝트 파일 구조

| 파일/폴더                 | 설명                                    |
| ------------------------- | --------------------------------------- |
| `{ProjectName}.mtproject` | XML 프로젝트 파일 (메인)                |
| `{NetworkName}.dbc`       | CAN 네트워크 데이터베이스               |
| `{NetworkName}.csv`       | 파라미터 CSV                            |
| `{NetworkName}.csf`       | CANmoon 설정                            |
| `{DeviceName}/`           | 디바이스별 CODESYS 프로젝트 폴더        |
| `{DeviceName}.exp`        | CODESYS 변수·POU 익스포트 (CDS 2.3)     |
| `{DeviceName}.pro`        | CODESYS 2.3 프로젝트                    |
| `script.dat`              | CODESYS 프로젝트 생성/업데이트 스크립트 |
| `{DeviceType}.tpl`        | CODESYS 2.3 템플릿                      |

### 주요 기능 목록 (매뉴얼 기반)

| 기능                   | 메뉴 경로                                         | 단축키 |
| ---------------------- | ------------------------------------------------- | ------ |
| New Project            | `File > New Project`                              | —      |
| Open Project           | `File > Open Project`                             | —      |
| Save Project           | `File > Save`                                     | Ctrl+S |
| Save As                | `File > Save as...`                               | —      |
| Export Project Archive | `File > Export Project Archive`                   | —      |
| Settings               | `File > Settings > Environment`                   | —      |
| System Export          | `Project > System Export` / Network Editor 아이콘 | —      |
| Export Parameter CSV   | 네트워크 hover → `Export > Export Parameter CSV`  | —      |
| CANdb Export           | 네트워크 hover 메뉴                               | —      |
| Add Device             | Network Editor `Add Device` 아이콘                | —      |
| Add Network            | Network Editor `Add Network` 아이콘               | —      |
| Delete Network         | 네트워크 우클릭 `Remove from Project`             | Del    |
| Configure Device       | 디바이스 더블클릭 → Configuration 탭              | —      |
| Object Dictionary      | Configuration → `Object Dictionary` 탭            | —      |
| PDO 설정               | Configuration → `PDO` 탭                          | —      |
| CAN 설정               | Configuration → `CAN` 탭                          | —      |
| Library Manager        | Library Manager 탭                                | —      |
| Create CODESYS Project | 디바이스 hover → `Create CODESYS Project`         | —      |
| Network Color          | 네트워크 hover → 색상 선택                        | —      |

---

## Plan

### 자동화 솔루션

WPF(.NET) 앱 → UIA 네이티브 지원

| 방법                    | 판정    | 근거                          |
| ----------------------- | ------- | ----------------------------- |
| pywinauto (UIA)         | 주 도구 | AutomationId 기반, WPF 최적   |
| pyautogui               | 보조    | hover 메뉴·스크린샷 캡처 전용 |
| AutoHotkey v2           | 제외    | Python 생태계와 분리          |
| PowerShell UIAutomation | 제외    | 코드 복잡                     |

### 조작 우선순위

| 순위 | 방법      | 조건                     |
| ---- | --------- | ------------------------ |
| 1    | 단축키    | 수집·검증 완료된 경우    |
| 2    | 메뉴 경로 | AutomationId 기반 탐색   |
| 3    | 화면 좌표 | 단축키·메뉴 모두 불가 시 |

### 실행 단계

| 단계 | 작업               | 상세                                                                    |
| ---- | ------------------ | ----------------------------------------------------------------------- |
| 1    | 버전 탐지          | `Program Files\Epec` 열거 → CHM MD5 비교 → 신규/변경 버전만 진행        |
| 2    | CHM 추출·파싱      | `hh.exe -decompile` → `chm_extracted/` 저장 → 버전 히스토리·기능명 수집 |
| 3    | 메뉴바 덤프        | `MultiTool.exe` 실행 → FILE/PROJECT/HELP 메뉴 순회 → 항목 수집          |
| 4    | 데모 프로젝트 생성 | 기존 스캔용 프로젝트 삭제 → New Project → CU-3606-21 디바이스 추가      |
| 5    | 컨텍스트 메뉴 수집 | 네트워크·디바이스 우클릭 → hover 메뉴 항목 수집                         |
| 6    | 단축키 수집        | UIA 읽기 → 검증 → `function_map.json` 기록                              |
| 7    | 기능 매핑          | 단축키 + 메뉴 경로 + 좌표 + 다이얼로그 구조 수집                        |
| 8    | 버전 diff          | 이전/현재 `ui_tree.json` 비교 → 변경 항목 재매핑                        |

### 스캔용 데모 프로젝트

| 항목      | 내용                                                            |
| --------- | --------------------------------------------------------------- |
| 경로      | `DemoProject/ScanDemo/ScanDemo.mtproject`                       |
| 생성 방식 | 매 스캔 시 기존 삭제 후 New Project로 신규 생성                 |
| 디바이스  | CU-3606-21 (컨텍스트 메뉴 수집 목적 — 네트워크·디바이스 필요)   |
| 사용 목적 | 우클릭 컨텍스트 메뉴, hover 메뉴 수집 전용 (실제 프로젝트 불변) |

### 단축키 수집

화면 표시 읽기 방식. 키 직접 입력은 검증 전용.

| 소스                   | 방법                                         | 우선순위 |
| ---------------------- | -------------------------------------------- | -------- |
| UIA `InputGestureText` | MenuItem 옆 단축키 텍스트 읽기 (`Ctrl+S` 등) | 1        |
| UIA `AccessKey`        | 밑줄 문자 읽기 → `Alt+{문자}` 변환           | 2        |
| 앱 리소스 파일         | 설치 폴더 XAML/resx → `KeyBinding` 추출      | 3        |

검증: 수집된 단축키 전송 → 기대 동작 확인 → `shortcut_verified: true/false`

### function_map.json 형식

```json
{
  "System Export": {
    "shortcut": "Ctrl+E",
    "shortcut_verified": true,
    "menu_path": ["Project", "System Export"],
    "automation_id": "MenuItemSystemExport",
    "coordinates": [120, 45],
    "dialog": "none"
  }
}
```

| 필드                | 설명                                |
| ------------------- | ----------------------------------- |
| `shortcut`          | UIA/리소스로 수집, 검증 완료된 것만 |
| `shortcut_verified` | 실 키 입력 테스트 결과              |
| `menu_path`         | 2순위 fallback                      |
| `automation_id`     | 안정적 탐색용 UIA ID                |
| `coordinates`       | 3순위 fallback, BoundingRect 중심   |
| `dialog`            | 실행 후 열리는 다이얼로그 UIA 참조  |

### 스크립트 구성 (`skills/fnscan/`)

| 스크립트      | 역할                                              |
| ------------- | ------------------------------------------------- |
| `version.py`  | 설치 버전 탐지, CHM 해시 비교                     |
| `chm.py`      | CHM 추출, 버전 히스토리·기능 파싱                 |
| `uitree.py`   | MultiTool 실행, 메뉴바·컨텍스트 메뉴 수집         |
| `mapper.py`   | UI 트리 → `function_map.json` 생성                |
| `diff.py`     | 버전 간 diff, 변경 기능 리포트                    |
| `verify.py`   | 단축키 일괄 검증, `shortcut_verified` 갱신        |
| `coverage.py` | 커버리지 체크 (기준 90%)                          |
| `run.py`      | 전체 순차 실행 진입점 (`py skills/fnscan/run.py`) |

---

## Generate

실행: `py skills/fnscan/run.py`

| 파일                                      | 함수                     | 역할                                                   |
| ----------------------------------------- | ------------------------ | ------------------------------------------------------ |
| [version.py](../skills/fnscan/version.py) | `get_installed_versions` | `Program Files\Epec` 열거 → `{버전: Path}` 반환        |
| [version.py](../skills/fnscan/version.py) | `needs_update`           | `meta.json` CHM MD5 비교 → 재처리 여부 판정            |
| [chm.py](../skills/fnscan/chm.py)         | `extract_chm`            | `hh.exe -decompile` → `chm_extracted/` 저장            |
| [chm.py](../skills/fnscan/chm.py)         | `parse_version_history`  | `VersionDifferences.htm` 파싱 → `version_history.json` |
| [uitree.py](../skills/fnscan/uitree.py)   | `dump_ui_tree`           | MultiTool 실행 → UIA 트리 순회 → `ui_tree_{ts}.json`   |
| [mapper.py](../skills/fnscan/mapper.py)   | `build_function_map`     | UIA 트리 → `function_map.json` (단축키·좌표 포함)      |
| [diff.py](../skills/fnscan/diff.py)       | `diff_function_maps`     | 이전/현재 `function_map.json` 비교 → `diff.json`       |

---

## Evaluate

### 검증 기준

| 항목           | 기준                                 | 판정 방법                                 |
| -------------- | ------------------------------------ | ----------------------------------------- |
| 기능 커버리지  | 매뉴얼 기능 목록 대비 ≥ 90%          | `function_map.json` 키 수 vs 매뉴얼 목록  |
| 단축키 정확도  | `shortcut_verified: true` 비율 ≥ 80% | `fnscan_verify.py` 일괄 전송·응답 확인    |
| UIA ID 안정성  | 재실행 시 동일 `automation_id` 유지  | 2회 덤프 diff → 변경된 ID 0개             |
| 좌표 유효성    | BoundingRect 화면 내 포함            | `rect[0] >= 0 and rect[1] >= 0`           |
| 버전 diff 누락 | 변경 버전에 diff 리포트 존재         | `docs/versions/{ver}/diff.json` 존재 확인 |

### 단축키 일괄 검증 ([verify.py](../skills/fnscan/verify.py))

`shortcut` 있는 항목마다 키 전송 → 다이얼로그 열림 여부로 `shortcut_verified` 갱신 → `function_map.json` 덮어쓰기

### 커버리지 체크 ([coverage.py](../skills/fnscan/coverage.py))

`function_map.json` 키 수 vs 매뉴얼 기능 목록(13개) → 비율 계산 → 90% 미만 시 누락 목록 출력

### 알려진 제약

| 항목                 | 내용                                                                     |
| -------------------- | ------------------------------------------------------------------------ |
| hover 전용 메뉴      | 네트워크·디바이스 우클릭 메뉴 — UIA 트리에 미노출, `pyautogui` 보조 필요 |
| 다이얼로그 내부 UIA  | 일부 커스텀 WPF 컨트롤은 `automation_id` 없음 → 좌표 fallback            |
| 버전별 레이아웃 변화 | 메뉴 순서 변경 시 `automation_id` 재수집 필요                            |
| CHM 없는 버전        | 8.1, 8.2 — CHM 추출 단계 skip, UIA 덤프만 수행                           |
