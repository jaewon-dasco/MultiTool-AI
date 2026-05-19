# MultiTool E2E 자동화 운영 지침

E2E UI 자동화 세션에서 MultiTool Creator 8.4를 다룰 때 반드시 따라야 할 규칙·패턴.

## 세션 종료 규칙 (의무)

테스트·probe·dry-run·야간 사이클 등 어떤 형태든 작업이 끝나면 **반드시 MultiTool 프로세스를 종료**한다.

```powershell
Get-Process | Where-Object { $_.ProcessName -like 'MultiTool*' } | ForEach-Object {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.SendKeys]::SendWait("%{F4}"); Start-Sleep -Milliseconds 1500
}
Start-Sleep -Seconds 2
Get-Process | Where-Object { $_.ProcessName -like 'MultiTool*' } | Stop-Process -Force
```

이유: 변경사항이 메모리에 남아 다음 세션에서 baseline 오염 → 노이즈 누적. Alt+F4 우선("Don't Save" 자동 처리 가정), 잔존 프로세스는 강제 종료로 폴백.

## UI 조작 규칙

### Click 메서드 선택

| 컨트롤 유형                         | 권장 메서드                               | 비권장                           |
| ----------------------------------- | ----------------------------------------- | -------------------------------- |
| 일반 Button/Hyperlink/Tab           | `element.click_input()`                   | `mouse.click(coords)`            |
| WPF DataGrid 셀 / RadTreeListView   | **`element.click_input()` 강제**          | `mouse.click(coords)` 동작 안 함 |
| Floating toolbar (이름 없는 Button) | `mouse.click(coords)` 허용 (rect 식별 후) | —                                |
| WPF Confirm/MessageBox              | `mouse.click(coords)` + win32 backend     | UIA 트리에 없음                  |

**핵심**: WPF DataGrid는 raw mouse event를 처리하지 않고 UIA InvokePattern을 통해서만 반응한다. `mouse.click(coords)`는 silent fail.

### 패널 진입 순서

```text
Network Editor → 디바이스 hyperlink invoke → floating toolbar 렌치 → Configure 패널 → 좌측 탭(CAN/J1939/Diagnostics/IO/...)
```

각 단계 사이 최소 1초 대기. tab 클릭 후 2초 대기(데이터 로드).

### I/O 패널 특수 처리

- **OCR 무력**: WPF DataGrid 셀은 비텍스트 렌더링 → winocr 결과 ~20건만, 핀 변수명·Mode 모두 누락
- **UIA로 직접 탐색**:
  - 행: `DataItem name='1.2'` (커넥터 번호.핀번호)
  - 모드: 행 y범위 내 Modes 컬럼(x≥410)의 `Button name='DI'/'DO'/'PWM'/'AI'/...`
- **커넥터 chevron**: 좌측 22px Button — `click_input()`으로 토글 (mouse.click 무력)
- **Variable Name 컬럼**: read-only Text. 변수명 변경은 이 테이블에서 불가능

### MultiTool 재시작 (야간 사이클)

```python
1. Alt+F4 → Alt+N (Don't Save)   # send_keys
2. taskkill /IM MultiTool.exe /F  # 폴백
3. subprocess.Popen([MULTITOOL_EXE])  # 인자 무시됨
4. UIA connect (최대 30s)
5. 디바이스 hyperlink 미감지 → Open Project... Hyperlink invoke → 경로 send_keys + Enter
6. 디바이스 hyperlink 노출 대기 (최대 12s)
```

## OCR vs UIA 선택 기준

| 상황                                    | 채널                                        |
| --------------------------------------- | ------------------------------------------- |
| CAN/J1939/Diagnostics 일반 라벨         | OCR + fuzzy_label_match                     |
| ComboBox 드롭다운 항목                  | OCR (드롭다운 펼친 후 캡쳐)                 |
| DataGrid 셀 / 표 행                     | **UIA only**                                |
| 짧은 헤더 텍스트 (Modes, Variable Name) | OCR 잘 잡힘                                 |
| 변수명·핀번호 (셀 내부)                 | **UIA only**                                |
| Floating toolbar 이름 없는 Button       | rect 기반 (`find_floating_toolbar_buttons`) |

## 알려진 함정

| 함정                                           | 상태    | 회피                                                       |
| ---------------------------------------------- | ------- | ---------------------------------------------------------- |
| Save 부수효과 (Guid·CobId 리셋 등 28건 노이즈) | 완화 중 | per-seed MultiTool 재시작 + baseline 정합화 (미진행)       |
| 네트워크 BitRate 강제 동기화                   | 해결    | device 단독 BitRate 변경 차단됨, NETWORK 노드에서만 가능   |
| Configure 패널 floating toolbar 일반 트리 부재 | 해결    | rect + size 필터로 식별                                    |
| WPF MessageBox UIA 미노출                      | 해결    | win32 backend + 좌표 클릭 (right-145=Yes, right-30=Cancel) |
| `Stop-Process MultiTool` 직접 사용             | 해결    | Alt+F4 → "Don't Save" 우선, taskkill은 폴백                |
| WPF DataGrid `mouse.click(coords)` silent fail | 해결    | UIA `click_input()` 강제 (위 "Click 메서드 선택")          |
| MultiTool 단일 인스턴스 + CLI 인자 무시        | 해결    | Open Project Hyperlink invoke + send_keys 경로로 우회      |
| OCR I/O 핀 변수명 미감지                       | 해결    | UIA 트리 직접 탐색 (`io_pin_recipe.py`)                    |

## 디바이스 템플릿 (권위 소스)

I/O 핀별 지원 모드, 기본값, 변수명은 디바이스 XML에 정의되어 있다.

```text
C:\Program Files (x86)\Epec\MultiTool Creator 8.4\Resources\Config\Devices\<model>.xml
```

| 요소                                  | 의미                                                         |
| ------------------------------------- | ------------------------------------------------------------ |
| `IO/Modes/Mode`                       | 모드 코드(2/3/4/7/...) → 이름(`#lang.IO.Mode.Di#` 등) 매핑   |
| `Pin/Id` + `Variable`                 | 핀 번호 + 기본 변수명 (X1_2, X1_3, ...)                      |
| `Pin/Scripts//TagCode/SupportedModes` | 해당 핀이 노출하는 모드 코드 (UNION으로 핀당 mode 집합 확정) |
| `Pin/DefaultMode`                     | 핀 초기 모드 코드                                            |

**활용**: `recipes/device_modes.py`로 파싱 → `pick_mode_for_pin()`로 valid mode 선택 → `scripts/generate_io_seeds.py`로 F_io.json 자동 생성. 시드 작성 시 mode 값을 추측하지 말고 항상 디바이스 템플릿에서 가져온다.

```python
from skills.e2e_explorer.recipes.device_modes import load_device, pick_mode_for_pin
d = load_device("3606_21")
print(d["pins"][2]["ui_labels"])   # → ['DI', 'DO', 'PWM', 'PI1 PW', ..., 'Step Motor']
```

## probe 스크립트 위치

| 스크립트                      | 목적                                                  |
| ----------------------------- | ----------------------------------------------------- |
| `probe_io_panel.py`           | I/O 탭 OCR 가시성 검증                                |
| `probe_io_uia.py`             | I/O 탭 UIA 트리 dump                                  |
| `probe_io_pin_click.py`       | 셀 클릭 후 컨트롤 변화 dump                           |
| `probe_io_collapse_v2.py`     | 커넥터 chevron expand/collapse 검증                   |
| `probe_io_variable_name.py`   | 핀 셀 우클릭/더블클릭/F2 결과 비교 — Edit 진입 경로   |
| `probe_od_predefined.py`      | OD Pre-defined 다이얼로그 트리 dump                   |
| `probe_od_dialog.py`          | OD 탭 toolbar 버튼 식별 시도                          |
| `probe_od_toolbar_all.py`     | OD 탭 모든 toolbar Button 위치 + 인접 Text dump       |
| `probe_od_buttons_id.py`      | OD toolbar 6 unnamed Button의 auto_id/class 확인      |
| `probe_od_click_btn1.py`      | OD toolbar Button[idx] 클릭 → 다이얼로그 등장 검증    |
| `probe_network_node.py`       | NETWORK 노드 선택 후 floating toolbar + UIA 변화 dump |
| `probe_network_panel_dump.py` | NETWORK 선택 후 좌측 패널 전체 dump (속성 위치)       |
| `probe_network_bitrate_*.py`  | Bit Rate 라벨 인접 컨트롤 식별 (수평/수직)            |
| `probe_net_toolbar.py`        | Network Editor 상단 toolbar Button/Hyperlink 식별     |

새 UI 패턴 만나면 동일 패턴(probe → JSON dump → 분석)으로 먼저 탐색 후 recipe 구현.

## 발견된 UI 패턴

| 패턴                         | 사용 위치                                 | 핸들러                                                          |
| ---------------------------- | ----------------------------------------- | --------------------------------------------------------------- |
| 라벨 우측 인접 컨트롤 (수평) | CAN Settings, J1939, Diagnostics          | `set_field_auto` (OCR + fuzzy_label_match)                      |
| 라벨 아래 컨트롤 (수직)      | NETWORK 노드 좌측 패널 (Bit Rate)         | `network_property.find_label_below_control`                     |
| 표 행/열 교차점              | Diagnostics Min/Max, I/O Modes 컬럼       | `set_field_auto(table_column=)` → `click_table_cell`            |
| WPF DataGrid Button cell     | I/O Modes (DI/DO/PWM/Step Motor)          | `io_pin_recipe.set_pin_mode` (UIA click_input)                  |
| 셀 더블클릭 → 우측 Edit      | I/O Variable Name                         | `io_pin_recipe.set_pin_variable_name`                           |
| Toolbar action + dialog      | A/D 카테고리 (Add Device, OD Pre-defined) | `toolbar_action_with_dialog` (✗ 미해결, 다이얼로그 자동화 필요) |

## SCHEDULE.md 운영

[docs/SCHEDULE.md](../../docs/SCHEDULE.md) — 작업 히스토리·진행·남은 항목 추적. 다음 시점에 갱신한다.

| 시점         | 갱신 내용                                              |
| ------------ | ------------------------------------------------------ |
| 작업 시작    | "진행 중" 표에 항목 추가, 상태 명시                    |
| 작업 완료    | "진행 중"에서 제거 → "완료" 표 상단에 commit 함께 기록 |
| 새 작업 발견 | "남은 작업" 표에 우선순위(★ 1~3) 부여 후 추가          |
| 블로커 발생  | 본 문서 "알려진 함정" 표에 추가 (SCHEDULE에는 미기재)  |

## 참조

- 시드 정의: `sequences_ui/{A,B,C,D,E,F}_*.json`
- 시드 실행: `recipes/seed_runner_ui.py` (`run_one_seed`)
- I/O 핀 모드: `recipes/io_pin_recipe.py`
- OCR 헬퍼: `recipes/ocr_helpers.py`
- 작업 스케줄: [docs/SCHEDULE.md](../../docs/SCHEDULE.md)
