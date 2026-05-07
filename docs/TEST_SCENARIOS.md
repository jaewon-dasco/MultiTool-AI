# MultiTool Vibe — 테스트 시나리오

vibe 스킬 + mtpatch + 자연어 자동화의 단계별 검증 절차.
저위험 → 고위험 순서. 각 단계 통과 후 다음 단계로.

## 사전 환경 체크

| #   | 항목               | 확인 명령                                                                     | 기대                             |
| --- | ------------------ | ----------------------------------------------------------------------------- | -------------------------------- |
| E1  | Python             | `py -3 --version`                                                             | Python 3.11+ 출력                |
| E2  | pywinauto          | `py -3 -c "import pywinauto; print(pywinauto.__version__)"`                   | `0.6.9` 등                       |
| E3  | anthropic SDK      | `py -3 -c "import anthropic; print(anthropic.__version__)"`                   | 미설치면 `pip install anthropic` |
| E4  | API 키             | `$env:ANTHROPIC_API_KEY -ne $null`                                            | `True`                           |
| E5  | MultiTool 8.4 설치 | `Test-Path "C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe"` | `True`                           |
| E6  | function_map.json  | `Test-Path docs\versions\8.4\function_map.json`                               | `True`                           |
| E7  | 샘플 .mtproject    | `Test-Path DemoProject\ScanDemo\ScanDemo.mtproject`                           | `True`                           |

**E1·E5·E6·E7만 충족하면 L0~L2 진행 가능. E3·E4는 L3 이상에서 필수.**

---

## L0 — 모듈 단위 회귀 (API·GUI 무관)

| #    | 명령                                                                    | 기대                                    |
| ---- | ----------------------------------------------------------------------- | --------------------------------------- |
| L0.1 | `py skills\vibe\selftest.py`                                            | `PASS=46  FAIL=0`                       |
| L0.2 | `py skills\vibe\debug_scenarios.py`                                     | `실 FAIL: 0 / EXPECTED 거절: 2 / OK: 9` |
| L0.3 | `py skills\expscan\run.py plan`                                         | 10개 카탈로그 출력, 모두 `todo`         |
| L0.4 | `py skills\expscan\run.py validate`                                     | `mapping.json 없음 — 캡처 0건`          |
| L0.5 | `py skills\mtpatch\run.py show DemoProject\ScanDemo\ScanDemo.mtproject` | `CAN1: bitrate=250 ...` 표시            |

---

## L1 — XML 패치 단독 (mtpatch CLI, GUI·API 무관)

테스트 전 백업: `cp ScanDemo.mtproject ScanDemo.mtproject.test-orig`. 종료 후 복구 권장.

| #    | 명령                                                                                     | 기대                                                    |
| ---- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| L1.1 | `py skills\mtpatch\run.py show DemoProject\ScanDemo\ScanDemo.mtproject`                  | bitrate=250, j1939=False                                |
| L1.2 | `py skills\mtpatch\run.py set-bitrate DemoProject\ScanDemo\ScanDemo.mtproject 1 500`     | `CAN1.BitRate = 500` + `backup: ...bak.YYYYMMDD_HHMMSS` |
| L1.3 | `py skills\mtpatch\run.py show DemoProject\ScanDemo\ScanDemo.mtproject`                  | bitrate=500 (변경 반영)                                 |
| L1.4 | `py skills\mtpatch\run.py set-bitrate DemoProject\ScanDemo\ScanDemo.mtproject 1 0`       | `[ERROR] invalid bitrate 0 ...` exit 1, 트레이스백 없음 |
| L1.5 | `py skills\mtpatch\run.py set-j1939 DemoProject\ScanDemo\ScanDemo.mtproject 1 true`      | `CAN1.J1939 = True` + 새 백업                           |
| L1.6 | `py skills\mtpatch\run.py set-buffering DemoProject\ScanDemo\ScanDemo.mtproject 1 false` | `CAN1.Buffering = False` + 백업                         |
| L1.7 | 백업 복구 → `py skills\mtpatch\run.py restore <project> <bak>`                           | `restored: ...bak.... → ScanDemo.mtproject`             |
| L1.8 | L1.7 후 `show` 재실행                                                                    | bitrate=250, j1939=False (원복)                         |

**Pass 기준**: 모든 set 명령에서 sibling `.bak.<timestamp>` 자동 생성, show 출력이 변경 반영, 잘못된 입력에 트레이스백 대신 [ERROR] + exit 1.

---

## L2 — vibe dry-run (실 Claude API + GUI 미조작)

비용 명령당 ~$0.05. dry-run은 GUI 미조작이라 안전. `--no-execute` 필수.

### L2.0 명령 형식

```
py skills\vibe\run.py "<자연어 명령>" --no-execute --project DemoProject\ScanDemo\ScanDemo.mtproject
```

출력 핵심: `final` (Claude 응답), `iter` (루프 횟수), `stop` (`end_turn` 정상), `usage` (토큰), `session log` (실행 시퀀스).

### L2.1 단일 기능 명령

| #      | 자연어 명령                 | 기대 session log                   | iter |
| ------ | --------------------------- | ---------------------------------- | ---- |
| L2.1.1 | `현재 프로젝트 저장`        | `Save Project via shortcut`        | 2~3  |
| L2.1.2 | `System Export 실행`        | `System Export via ...`            | 2~3  |
| L2.1.3 | `현재 디바이스 정보 보여줘` | `xml_show via ...` (XML 우회 선택) | 2~3  |
| L2.1.4 | `Help 매뉴얼 열어`          | `F1 Manual via shortcut(F1)`       | 2~3  |

### L2.2 다단계 명령

| #      | 자연어 명령                           | 기대 session log 시퀀스                                                                    | iter |
| ------ | ------------------------------------- | ------------------------------------------------------------------------------------------ | ---- |
| L2.2.1 | `ScanDemo 프로젝트 열어줘`            | `Open Project` → `wait` → `type_text(...ScanDemo.mtproject)` → `press_key(enter)` → `wait` | 3~5  |
| L2.2.2 | `현재 프로젝트 저장 후 System Export` | `Save Project` → `System Export`                                                           | 3~5  |
| L2.2.3 | `Save As로 ScanDemo_v2 저장`          | `Save As` → `wait` → `type_text(...ScanDemo_v2...)` → `press_key(enter)` → `wait`          | 3~5  |

### L2.3 XML 우회 — 단순 필드 변경

| #      | 자연어 명령                   | 기대 session log                                                                |
| ------ | ----------------------------- | ------------------------------------------------------------------------------- |
| L2.3.1 | `CAN1 bitrate를 500으로 설정` | `xml_set_bitrate(can_number=1, bitrate=500)` (Configure: CAN 다이얼로그 미사용) |
| L2.3.2 | `J1939 활성화`                | `xml_set_j1939(can_number=1, enabled=True)`                                     |
| L2.3.3 | `Buffering 비활성화`          | `xml_set_buffering(can_number=1, enabled=False)`                                |
| L2.3.4 | `현재 CAN 설정 보여줘`        | `xml_show` → 결과에 cans·devices 포함                                           |

### L2.4 도메인 위반 — 거절 동작

| #      | 자연어 명령              | 기대                                                              |
| ------ | ------------------------ | ----------------------------------------------------------------- |
| L2.4.1 | `bitrate를 333으로 설정` | LLM이 화이트리스트 안내 후 사용자 재확인 요청 (거절·재질문)       |
| L2.4.2 | `프로젝트 닫기`          | LLM이 "Close Project 단독 기능 없음" 안내, Open Project 대안 제시 |
| L2.4.3 | `NodeId를 0으로 설정`    | LLM이 도메인 위반 안내                                            |

### L2.5 캐시 효과 검증

L2.1.1을 **연속 2회** 실행 → 두 번째 실행에서 `cache_read` ≫ 0 확인.

| 회차 | usage 패턴                                            |
| ---- | ----------------------------------------------------- |
| 1    | `cache_creation_input_tokens` ≫ 0, `cache_read = 0`   |
| 2    | `cache_read_input_tokens` ≫ 0 (tools+system 캐시 hit) |

**Pass 기준**: cache_read 비율 ≥ 50% (2회차).

---

## L3 — vibe 실 GUI 조작 (전체 종단 검증)

**위험**: pywinauto가 화면을 점유하고 실 클릭 발생. 다른 창 작업 중지 권장.

### 사전 작업

1. 모든 다른 창 minimize
2. MultiTool 자동으로 시작됨 — 설치 경로 확인
3. 백업: `cp ScanDemo.mtproject ScanDemo.mtproject.l3-orig`

### L3.1 안전한 단일 명령

```
py skills\vibe\run.py "현재 프로젝트 저장" --project DemoProject\ScanDemo\ScanDemo.mtproject
```

| 관찰 항목      | 기대                               |
| -------------- | ---------------------------------- |
| MultiTool 시작 | 자동 실행, ScanDemo 자동 로드      |
| Save 동작      | 화면에 변화 없음 (저장만)          |
| stop_reason    | `end_turn`                         |
| 사후 상태      | `.mtproject` mtime 갱신, 내용 동일 |

### L3.2 정보 조회 (read-only)

```
py skills\vibe\run.py "현재 디바이스 정보" --project DemoProject\ScanDemo\ScanDemo.mtproject --before before.json --after after.json
```

| 관찰 항목 | 기대                                  |
| --------- | ------------------------------------- |
| diff      | 모든 카테고리 빈 배열 (변경 없음)     |
| final     | LLM이 EPEC_CU1, 3606_21.xtmpl 등 언급 |

### L3.3 XML 우회 — 실 변경 + 검증

```
py skills\vibe\run.py "CAN1 bitrate 500으로 변경" --project DemoProject\ScanDemo\ScanDemo.mtproject --before before.json --after after.json
```

| 관찰 항목   | 기대                                |
| ----------- | ----------------------------------- |
| MultiTool   | (이상적으로) 미실행 — XML 직접 편집 |
| .bak.<ts>   | sibling 백업 파일 생성              |
| diff (snap) | networks 카테고리에 변경 가능성     |
| 검증        | `mtpatch show`로 bitrate=500 확인   |

테스트 후 백업으로 복구: `py skills\mtpatch\run.py restore ScanDemo.mtproject ScanDemo.mtproject.bak.<ts>`

### L3.4 다단계 GUI 명령

**주의: 위험 명령. 백업 필수.**

```
py skills\vibe\run.py "ScanDemo 프로젝트 열고 저장 후 System Export"
```

| 관찰 항목                                   | 기대                     |
| ------------------------------------------- | ------------------------ |
| 다이얼로그 자동 처리 (Open Project 후 경로) | 시퀀스 정상 진행         |
| stop_reason                                 | `end_turn`               |
| `.mtproject` 무결성                         | XML 깨짐 없음            |
| Export 산출물                               | 프로젝트 디렉토리에 생성 |

---

## L4 — variant 캡처 (실 누적)

`skills/expscan/run.py plan`의 10개 카탈로그를 채우는 절차.

각 variant마다 반복:

| 단계 | 명령·작업                                                       |
| ---- | --------------------------------------------------------------- |
| 1    | MultiTool에서 ScanDemo 열기 (baseline 상태 확인)                |
| 2    | UI에서 단일 설정 변경 (예: Configure: CAN → Bit Rate 250 → 500) |
| 3    | `Ctrl+Alt+E` (System Export)                                    |
| 4    | `py skills\expscan\run.py capture <label>` — 예: `bitrate_500`  |
| 5    | `py skills\expscan\run.py diff baseline <label>`                |
| 6    | `py skills\expscan\run.py mapping <label> "변경 설명"`          |
| 7    | UI에서 baseline 상태로 되돌림 (다음 variant 준비)               |

10개 완료 후:

```
py skills\expscan\run.py validate
```

기대: errors 0, warnings 0, 카탈로그 미수집 0.

---

## 트러블슈팅

| 증상                             | 원인 후보                                | 처방                                    |
| -------------------------------- | ---------------------------------------- | --------------------------------------- |
| `ModuleNotFoundError: anthropic` | SDK 미설치                               | `pip install anthropic`                 |
| `401 unauthorized`               | 키 미설정·만료                           | `$env:ANTHROPIC_API_KEY="sk-..."`       |
| `iter=12 stop=max_iterations`    | LLM이 시퀀스 미수렴                      | 명령 더 구체화 또는 `--max-iter` 증가   |
| `cache_read=0` 반복              | tools 마지막 항목 변경되었거나 모델 변경 | function_map 재빌드 또는 모델 고정      |
| `via coords(...)` 다수           | shortcut_verified=False 항목들           | `py skills\fnscan\verify.py 8.4`        |
| 다이얼로그가 안 닫힘             | type_text·press_key 시퀀스 누락          | 사용자 수동 닫기 → system 프롬프트 보강 |
| `.mtproject` XML 파싱 에러       | 손상·다른 버전                           | `restore` 백업으로 복구                 |
| MultiTool 미실행                 | 경로 다름·버전 차이                      | settings.local.json 권한 확인           |

---

## 위험 가드 — 반드시 준수

| 규칙                                                                |
| ------------------------------------------------------------------- |
| L1·L3 진행 전 항상 `.mtproject` 사본 백업 (`*.test-orig` 등)        |
| `Remove from Project`·`Save As` 같은 파괴적 명령은 백업 후에만 실행 |
| `--no-execute` dry-run 먼저 통과 → 실 실행으로 진행                 |
| 다단계 명령은 한 단계씩 분해해서 첫 실행                            |
| 실행 중 의도치 않은 다이얼로그 발생 시 즉시 ESC                     |
| API 키는 코드·MD에 하드코딩 금지                                    |

---

## 결과 보고 양식

이슈 발견 시 다음 정보 첨부:

```
시나리오: L2.3.1
명령:     "CAN1 bitrate를 500으로 설정"
기대:     xml_set_bitrate(can_number=1, bitrate=500)
실제:     configure_can(...)  ← XML 우회 선택 안 함
usage:    in=5234 out=128 cache_read=4920 cache_creation=0
session log:
  - Configure: CAN via menu(Configure > CAN)
final:    "..."
재현:     항상 / 가끔 / 1회만
```
