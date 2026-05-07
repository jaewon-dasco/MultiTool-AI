---
name: multitool
description: EPEC MultiTool Creator GUI 자동 조작 또는 .mtproject XML 직접 편집을 자연어 명령으로 수행. /multitool <자연어 명령> 형태로 호출. 디바이스 추가·CAN 설정·OD 편집·System Export·CODESYS 생성·BitRate/Buffering/J1939/NodeId/Heartbeat 변경 등. 키워드 — MultiTool, Epec, .mtproject, .exp, ScanDemo, CU-3606, Bitrate, BitRate, OD index, RPDO, TPDO, System Export, CODESYS, Add Device, Configure CAN, J1939, ISOBUS, Buffering, NodeId, Heartbeat, NETWORK1.dbc.
---

# multitool — 인터랙티브 실행 가이드

`/multitool <자연어 명령>` 형태로 호출됨. 본 스킬이 트리거되면 Claude(현재 세션의 나)가 다음 절차를 따른다.

## 실행 원칙

- **본 세션의 Claude가 직접 의사결정하고 명령 실행한다.** `agent.py`(별도 Anthropic API 호출)는 호출하지 않는다 — 이미 LLM(나)이 사용자와 대화 중이므로 추가 API 호출은 비용 낭비.
- Bash/PowerShell tool로 `skills/mtpatch/` CLI 또는 `skills/vibe/run.py`를 실행해 결과를 사용자에게 보고.
- **위험 명령은 사용자 명시 확인 후에만 실행** (Save As, 파괴적 변경, 앱 종료).

## 의사결정 트리

```
사용자 명령 →
  ┌─ 정보 조회 (CAN 설정, 디바이스 목록 등) → mtpatch show
  ├─ 단일 XML 필드 변경 (BitRate/Buffering/J1939/NodeId/Heartbeat) → mtpatch set-* (GUI 우회)
  ├─ GUI 단일 기능 (Save Project, System Export, Help 등) → vibe/run.py "..." [--no-execute]
  ├─ 다단계 GUI (Open + 변경 + Save 등) → vibe/run.py "..." (또는 단계 분해)
  └─ 도메인 위반 (bitrate=333 등) → 사용자에게 거절·재질문
```

## 실행 명령 매핑

### 정보 조회 (안전, 즉시 응답)

```bash
py -3 skills/mtpatch/run.py show <project>
```

LLM은 출력의 핵심 필드(bitrate/buffering/j1939/devices)를 사용자에게 정리해 전달.

### XML 직접 편집 (GUI 우회, 자동 백업)

```bash
py -3 skills/mtpatch/run.py set-bitrate   <project> <can#> <kbps>
py -3 skills/mtpatch/run.py set-buffering <project> <can#> <true|false>
py -3 skills/mtpatch/run.py set-j1939     <project> <can#> <true|false>
py -3 skills/mtpatch/run.py set-node-id   <project> <can#> <id>
py -3 skills/mtpatch/run.py set-heartbeat <project> <can#> <ms>
```

**유효 BitRate**: `{10, 20, 50, 100, 125, 250, 500, 800, 1000}` kbps. 그 외 값 요청 시 사용자에게 거절·재질문.

각 명령 자동 sibling `.bak.<timestamp>` 생성. 실행 후 mtpatch show로 변경 확인 권장.

### GUI 자동화 (실 클릭, 위험)

```bash
py -3 skills/vibe/run.py "<자연어>" --project <project>             # 실 GUI
py -3 skills/vibe/run.py "<자연어>" --project <project> --no-execute  # dry-run
```

**의존**: `pip install anthropic` + `ANTHROPIC_API_KEY`. 미충족 시 사용자에게 알리고 mtpatch 우회 가능 여부 검토.

**첫 실행은 항상 `--no-execute` dry-run 권장**.

## 인자 파싱 가이드

사용자 자연어에서 추출:

| 추출 대상  | 패턴                                 | 예                                  |
| ---------- | ------------------------------------ | ----------------------------------- |
| 프로젝트명 | "ScanDemo", "<이름> 프로젝트"        | DemoProject/<이름>/<이름>.mtproject |
| CAN 번호   | "CAN1", "CAN 1", "1번 CAN"           | 1                                   |
| Bitrate    | "500kbps", "500 kbit", "500"         | 500                                 |
| ON/OFF     | "활성/비활성", "켜/꺼", "true/false" | true/false                          |
| Hex 인덱스 | "0x2300", "2300h"                    | int(s, 16)                          |

프로젝트 경로 모호 시 사용자에게 확인:

```
사용 가능한 .mtproject:
  - DemoProject/NewProject/NewProject.mtproject
  - DemoProject/ScanDemo/ScanDemo.mtproject
어느 프로젝트인가요?
```

## 응답 형식

각 명령 실행 후 다음 구조로 사용자에게 보고:

```
[실행] mtpatch set-bitrate ScanDemo.mtproject 1 500
[결과] CAN1.BitRate = 500
[백업] ScanDemo.mtproject.bak.20260507_103045
[검증] mtpatch show 확인 시 bitrate=500 반영
```

오류 시:

```
[거절] bitrate 333은 유효 화이트리스트 외
[허용 값] 10, 20, 50, 100, 125, 250, 500, 800, 1000 kbps
[재질문] 어느 값으로 설정할까요?
```

## 안전 규칙

| 규칙                                                                        |
| --------------------------------------------------------------------------- |
| 파괴적 명령(Remove from Project, Save As 덮어쓰기 등)은 사용자 확인 후 실행 |
| 첫 GUI 자동화는 항상 `--no-execute` dry-run                                 |
| BitRate·NodeId·Heartbeat 등 도메인 위반 입력은 거절·재질문                  |
| `_generated.exp`·`.pro` 직접 편집 금지                                      |
| API 키·credentials를 출력에 노출 금지                                       |

## 예시 — 완전 흐름

**사용자**: `/multitool can 속도 500으로 변경`

**Claude 추론**:
- 의도: BitRate 변경 → XML 우회 가능
- 인자 파싱: CAN 번호 미명시 → CAN1로 추정 또는 사용자 확인
- 프로젝트 미명시 → 사용 가능한 .mtproject 목록 확인 → 사용자 확인

**Claude 응답**:
```
어느 프로젝트의 CAN 속도를 변경할까요?
1. DemoProject/ScanDemo/ScanDemo.mtproject (현재 250kbps)
2. DemoProject/NewProject/NewProject.mtproject

또한 CAN1만 변경하시면 될까요?
```

**사용자**: `1번, CAN1로`

**Claude**:
```
[실행] py -3 skills/mtpatch/run.py set-bitrate DemoProject/ScanDemo/ScanDemo.mtproject 1 500
```

(Bash tool로 실행, 결과 파싱)

```
[결과] CAN1.BitRate = 500
[백업] ScanDemo.mtproject.bak.20260507_103045
[검증] mtpatch show 결과 bitrate=500 확인됨
```

---

## 참고 산출물

| 경로                                  | 내용                                 |
| ------------------------------------- | ------------------------------------ |
| `skills/mtpatch/run.py`               | XML 직접 편집 CLI (GUI 우회)         |
| `skills/vibe/run.py`                  | LLM tool 루프 (헤드리스·외부 호출용) |
| `skills/multitool/SKILL.md`           | 프로젝트 아키텍처 문서               |
| `docs/PROJECT.md`                     | 5섹션 명세                           |
| `docs/TEST_SCENARIOS.md`              | 테스트 절차                          |
| `docs/versions/8.4/function_map.json` | 49개 GUI 기능 정의                   |
