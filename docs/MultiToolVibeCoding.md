# MultiToolVibeCoding

자연어 명령으로 EPEC MultiTool을 조작해 `.mtproject` 산출물을 생성·수정하는 시스템.
[MultiToolScan](MultiToolScan.md) 산출물을 LLM tool surface로 활용한다.

## Clarify

| 항목      | 내용                                                                         |
| --------- | ---------------------------------------------------------------------------- |
| 입력      | 자연어 명령 + 대상 `.mtproject` (없으면 신규)                                |
| 출력      | MultiTool UI 조작 → `.mtproject` / CSV / dbc 산출물                          |
| 대상 작업 | 디바이스 편집, 네트워크 설정, OD 편집, PDO 매핑, System Export, CODESYS 생성 |
| 제약      | `function_map.json` 의존 — 미수집 기능은 처리 불가                           |
| 외부 의존 | MultiToolScan 산출물 + Claude API (function calling)                         |

### 사용 예

| 명령                                      | 호출 시퀀스                  |
| ----------------------------------------- | ---------------------------- |
| "CU-3606-21 추가하고 CAN1 250kbps로 설정" | Add Device → Configure: CAN  |
| "ScanDemo 열고 OD 0x2300 추가"            | Open Project → OD: Add Index |
| "비례밸브 RPDO 매핑 추가"                 | Configure: PDO → 매핑 입력   |
| "현재 프로젝트 System Export"             | System Export                |

---

## Context Gather

### 외부 의존성

| 산출물                                  | 역할                                |
| --------------------------------------- | ----------------------------------- |
| `docs/versions/{ver}/function_map.json` | 기능명 → UI 시퀀스 (단축키·좌표·탭) |
| `docs/PROJECT.md`                       | 프로젝트 구조·파라미터·OD 인덱스    |
| `docs/MultiToolScan.md`                 | 수집·검증 방식                      |
| Claude API                              | 자연어 → tool call 변환             |

### 의도 분류 (function_map 기반)

| 의도          | 함수 (`function_map.json` 키)                                               |
| ------------- | --------------------------------------------------------------------------- |
| 프로젝트 관리 | New Project, Open Project, Save Project, Save As..., Export Project Archive |
| 디바이스 편집 | Add Device, Add Slave Device, Remove from Project, Clone Unit, Connect      |
| 네트워크 편집 | Add Network, Configure: CAN/CANopen/J1939/NMEA 2000                         |
| OD 편집       | Configure: Object Dictionary + OD toolbar 8개                               |
| 통신 설정     | Configure: PDO, Address Claiming, ISOBUS                                    |
| Export        | System Export, Export Device                                                |
| Help          | F1 Manual, F2 About                                                         |

### 자연어 → 파라미터 매핑

| 자연어        | 추출 필드                              | 예                                        |
| ------------- | -------------------------------------- | ----------------------------------------- |
| 디바이스 식별 | ProductFamily/Device/FunctionalVersion | "CU-3606-21" → 3000 series, 3606, 3606-21 |
| OD 인덱스     | hex 16-bit                             | "0x2300", "2200h"                         |
| Bitrate       | 정수                                   | "250kbps", "500K"                         |
| 단위 변환     | 0.01V, 0.1°C 등                        | "12V" → `1200`                            |

---

## Plan

### 시스템 구조

```
자연어 명령
    ↓
Claude API (function calling, tools=function_map 변환)
    ↓
tool_use 블록 → function_map 항목 lookup
    ↓
UI Automation 실행 (pywinauto, 단축키 우선)
    ↓
.mtproject XML diff → 의도 일치 검증
```

### 실행 단계

| 단계 | 작업           | 상세                                                   |
| ---- | -------------- | ------------------------------------------------------ |
| 1    | 명령 파싱      | LLM이 자연어 → tool call 시퀀스 변환                   |
| 2    | MultiTool 시작 | 대상 프로젝트 로드 (없으면 New Project)                |
| 3    | 시퀀스 실행    | tool_use → function_map → UI 조작 (단축키 → 좌표 폴백) |
| 4    | 상태 추적      | 각 단계 후 활성 다이얼로그·탭·트리 노드 확인           |
| 5    | 검증·저장      | `.mtproject` XML diff → Save Project → close           |

### 조작 우선순위 (MultiToolScan과 동일)

| 순위 | 방법      | 조건                             |
| ---- | --------- | -------------------------------- |
| 1    | 단축키    | `shortcut_verified: true`인 경우 |
| 2    | 메뉴 경로 | `menu_path` + UIA 탐색           |
| 3    | 화면 좌표 | 1·2 모두 불가 시                 |

### Tool 스키마 변환

`function_map.json` 49개 항목 → Claude API tool schema 자동 생성:

```python
def to_tool(name: str, info: dict) -> dict:
    return {
        "name": name.replace(" ", "_").replace(":", "").lower(),
        "description": f"{name} (단축키: {info['shortcut'] or 'none'}, source: {info['source']})",
        "input_schema": {"type": "object", "properties": _params_for(info)},
    }
```

다이얼로그 입력 필드는 `device_config` 항목의 `inputs`에서 파라미터 추출.

### 스크립트 구성 (`skills/vibe/`)

| 스크립트     | 역할                                               |
| ------------ | -------------------------------------------------- |
| `tools.py`   | function_map → tool schema + 실행 wrapper          |
| `params.py`  | 자연어 → 파라미터 추출 (디바이스명·hex·bitrate 등) |
| `agent.py`   | Claude API tool 루프                               |
| `session.py` | MultiTool 인스턴스 + 프로젝트 상태 추적            |
| `verify.py`  | `.mtproject` XML diff 기반 의도 일치 검증          |
| `run.py`     | CLI 진입점 (`py skills/vibe/run.py "명령"`)        |

---

## Generate

### Claude API 호출 루프

```python
from anthropic import Anthropic
client = Anthropic()
tools  = build_tools("docs/versions/8.4/function_map.json")
msgs   = [{"role": "user", "content": user_cmd}]

while True:
    resp = client.messages.create(
        model="claude-opus-4-7", max_tokens=4096,
        tools=tools, messages=msgs,
    )
    msgs.append({"role": "assistant", "content": resp.content})
    if resp.stop_reason != "tool_use":
        break
    results = [exec_tool(b) for b in resp.content if b.type == "tool_use"]
    msgs.append({"role": "user", "content": results})
```

### 실행 예 — "CU-3606-21 디바이스 추가"

| 단계 | tool_use     | UI 조작 (function_map 참조)    |
| ---- | ------------ | ------------------------------ |
| 1    | new_project  | Ctrl+Shift+N → 폴더 선택       |
| 2    | add_device   | NE 툴바 `Add Device` 좌표 클릭 |
| 3    | (cascading)  | 3000 series → 3606 → 3606-21   |
| 4    | save_project | Ctrl+S                         |

### Prompt Cache 적용

`tools` 배열 + `function_map.json` 컨텍스트는 caching 대상 (정적 + 토큰 큼). 명령마다 cache hit으로 응답 속도·비용 절감.

---

## Evaluate

### 검증 기준

| 항목        | 기준                               | 판정                    |
| ----------- | ---------------------------------- | ----------------------- |
| 의도 일치   | 산출물 == 기대 .mtproject XML      | gold sample diff 0 라인 |
| 실행 성공률 | 우선 시나리오 100% 완료            | 5개 시나리오 자동 회귀  |
| 응답 시간   | 단순 명령 ≤ 60초                   | 시나리오 1~3            |
| 복구        | UI 실패 시 명확 에러 + 상태 롤백   | 의도적 실패 주입        |
| 단축키 활용 | `shortcut_verified` 항목 우선 사용 | 실행 로그 분석          |

### 한계

| 항목          | 내용                                                            |
| ------------- | --------------------------------------------------------------- |
| 기능 커버리지 | function_map 49개 — Export Parameter CSV·CANdb Export 등 미수집 |
| 단축키 검증   | 7/12 (58.3%) — 미검증 5개는 좌표/메뉴 폴백                      |
| 동시성        | 단일 MultiTool 인스턴스 — 병렬 실행 불가                        |
| Headless 불가 | GUI 자동화 — 사용자 화면 점유                                   |
| 의도 모호성   | "비례밸브 설정" 같은 추상 명령 → 추가 명세 필요                 |

### 회귀 시나리오

| #   | 시나리오                               | 기대 산출물                   |
| --- | -------------------------------------- | ----------------------------- |
| 1   | "DemoProject로 CU-3606-21 새 프로젝트" | `.mtproject` + Devices 1개    |
| 2   | "ScanDemo 열고 OD 0x2300 추가"         | OD 트리에 0x2300 등장         |
| 3   | "CAN1 250kbps 설정"                    | `<CanConfig Bitrate="250"/>`  |
| 4   | "현재 프로젝트 System Export"          | export 디렉토리에 산출물 생성 |
| 5   | "CODESYS 프로젝트 생성"                | `{Device}/{Device}.pro` 생성  |
