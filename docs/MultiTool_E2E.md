# MultiTool E2E 자율 학습 시스템 구축

| 항목   | 값         |
| ------ | ---------- |
| 작성일 | 2026-05-14 |
| 상태   | 진행 중    |
| Commit | —          |

야간 자율 탐색(Gemma4) + 주간 자동 감독(Claude routine) 2-Tier 구조로 MultiTool GUI 전체 기능을 학습하고 `.exp` 파일을 자동 생성하는 E2E 에이전트.

**학습 완료 정의**: `skills/e2e_explorer`가 사람/Claude 개입 없이 MultiTool 전 기능 제어 + `.exp` 생성을 수행할 수 있는 상태. 자율도 지표가 Sunset 임계를 모두 충족하면 Claude routine을 자동 비활성화(W6)하고 skill 단독 운영으로 전환한다.

## 아키텍처 (2-Tier)

```text
┌─ 야간 00:00~05:30 ─────────────────────────────────────────┐
│                                                            │
│  Task Scheduler ─► nightly_run.ps1 ─► orchestrator.py      │
│                                            │               │
│                              ┌─────────────┼────────────┐  │
│                              ▼             ▼            ▼  │
│                       Gemma4 (Mac)    pywinauto    xml_utils│
│                       JSON 의사결정   GUI 조작     XML 패치 │
│                              │             │            │  │
│                              └─────────────┼────────────┘  │
│                                            ▼               │
│                                  KB (SQLite/JSONL)         │
│                                  logs/e2e/<date>/ 산출물   │
└────────────────────────────────────────────────────────────┘
                            │ (05:30 봉인)
                            ▼
┌─ 주간 09:00 ───────────────────────────────────────────────┐
│                                                            │
│  Claude routine (schedule 스킬 cron)                       │
│   └─► /review-last-night                                   │
│         1) summary.md 읽기                                 │
│         2) auto_approve_policy 분류                        │
│         3) 안전 변경 → e2e/auto/<date> 브랜치 commit       │
│         4) 위험 변경 → review_queue.jsonl 적재             │
│         5) next_night_hints.json 갱신 ─► 다음 야간 주입    │
│         6) docs/tasks/<date>_e2e-review.md 기록            │
│         7) 자율도 지표 평가 → Sunset 충족 시 W6 트리거     │
└────────────────────────────────────────────────────────────┘
```

| 시간대      | 주체         | 역할                                                 | 비용 |
| ----------- | ------------ | ---------------------------------------------------- | ---- |
| 00:00~05:30 | Gemma4 (Mac) | 자율 탐색·실행·자기검증·KB 누적                      | 무료 |
| 05:30       | OS           | 프로세스 종료 + VM 스냅샷 복구                       | —    |
| 09:00       | Claude       | 산출물 검토·스킬 개선·hints 갱신·HITL 큐·Sunset 판정 | 구독 |

## 완료조건

- 00:00~05:30 무인 자동 실행 + 05:30 클린 복구 1사이클 무중단 통과
- 09:00 Claude routine 1회 자동 실행 + `auto_approve_policy` 분류·git commit·hints 갱신 완료
- 골든 `.exp` 대비 의미적 동등성을 통과한 자동생성 `.exp` 1건 이상 산출
- Claude routine을 통해 `verified=true`로 승격된 워크플로우 1건 이상 KB에 등록
- 4단계 학습 프로토콜 1주기 완주 — 관찰→패턴 추출→XML/`.exp` 직접 합성→round-trip 검증 통과 사례 1건 이상
- 자율도 지표 5개(`feature_coverage`/`self_validate_pass_rate`/`regression_count`/`synthesis_accuracy_xml`/`synthesis_accuracy_exp`) Sunset 임계 충족 시 W6 자동 트리거 검증

## 금지조건

- 유료 API 키 사용 금지 (야간) — 추론은 원격 Mac mini Ollama `gemma4:26b`(Apache 2.0)만 사용
- 야간 사이클 중 Claude Code 호출 금지 — Claude는 09:00 routine에서만 동작
- Gemma4의 직접 `verified=true` 승격 금지 — 야간은 `unverified`만, 승격은 Claude routine 권한
- HITL 미승인 워크플로우의 Phase B(생산 단계) 사용 금지 — `verified=false`는 탐색에만 사용
- Claude routine의 `main` 브랜치 직접 commit 금지 — 매번 `e2e/auto/<date>` 브랜치
- Claude routine의 일일 변경 라인수 상한(기본 100) 초과 시 자동 적용 금지 → `review_queue.jsonl` 적재
- 액션 전 `.mtproject` 백업·VM 스냅샷 없이 파괴적 변경 금지
- Tailscale 외 인터넷 노출(Funnel/포트포워딩) 금지 — tailnet 내부만 허용
- 본 작업 범위 외 MultiTool 프로젝트 파일(`MultiToolProject/`) 임의 수정 금지 — 학습/검증은 `MultiToolProject/E2EProject/`에서만 수행
- `docs/exp_patterns/`·`docs/versions/8.4/function_map.json` 참조 자산 변경 금지 (Claude routine 높음 위험 큐로만 처리)
- 복합 GUI 시퀀스 한 번에 실행 금지 — 항상 원자 액션 단위로 분해, 분해 불가 시 `failures.jsonl`에 `reason="non_atomic"` 기록 후 백트래킹
- `.exp`의 `(*START - Implicit variables ...*)` 이하 블록은 합성 대상·diff 비교 모두 제외 — EPEC Parser 자동 생성 영역
- Gemma4가 `kb/patterns/xml_rules.jsonl`·`exp_rules.jsonl` 직접 작성 금지 — 후보는 `_candidates.jsonl`에만, 승급은 Claude routine

## 검증조건

| 단계         | 검증 방법                                                                                 |
| ------------ | ----------------------------------------------------------------------------------------- |
| 백엔드 ready | `curl https://macmini.tailed5292.ts.net:11434/api/tags` → 200 + `gemma4:26b` 존재         |
| W1 PoC       | pywinauto 컨트롤 트리 JSON dump 성공 + Gemma4가 메뉴 분류 JSON 응답 반환                  |
| W2 KB        | `kb/controls.sqlite` 생성 + Device 추가 후보 워크플로우 1건 `unverified` 기록             |
| W3 자율루프  | 1시간 dry-run 로그에서 미방문 컨트롤 10개 이상 신규 탐색 기록                             |
| W3 routine   | `/schedule` 등록된 09:00 cron 1회 트리거 + `auto_approve_policy` 분류 결과 로그 확인      |
| W4 야간운영  | Task Scheduler 00:00 트리거 + 05:30 강제종료 Task + `-RestartCount` 자동 재시도 동작 확인 |
| W4 양방향    | `next_night_hints.json` 갱신 후 다음 야간 orchestrator가 hints를 프롬프트에 주입했는지    |
| W5 산출물    | `exp_validator`로 자동생성 `.exp` 파싱 → 골든 의미적 diff 0 통과                          |
| W5 승급      | Claude routine이 `unverified` → `verified` 승급 1건 commit 기록                           |
| W2.5 관찰    | `kb/observations/` 페어 10건 이상 누적 (XML before/after + .exp before/after)             |
| W3.5 패턴    | Gemma 후보 → Claude 검증 → `xml_rules.jsonl`/`exp_rules.jsonl` 승급 규칙 1건 이상         |
| W5.5 합성    | `mtproject_writer`·`exp_writer`로 단순 목표 1건 합성 → round-trip 의미적 diff 0           |

## 작업 계획

### 확정된 환경

| 항목       | 값                                                                           |
| ---------- | ---------------------------------------------------------------------------- |
| 추론 위치  | 원격 Mac mini (Tailscale)                                                    |
| Base URL   | `https://macmini.tailed5292.ts.net:11434`                                    |
| 모델       | `gemma4:26b` (Gemma 4 26B A4B MoE, 활성 ~4B, 32 tok/s, 2026-04-02 공식 출시) |
| 라이선스   | Apache 2.0                                                                   |
| 응답 구조  | reasoning — `message.thinking` + `message.content`                           |
| Keep-alive | `"8h"`                                                                       |

### 컴포넌트

| 컴포넌트         | 역할                                      | 기술                                   |
| ---------------- | ----------------------------------------- | -------------------------------------- |
| Orchestrator     | 야간 의사결정 루프·목표관리               | Python + LangGraph (또는 FSM)          |
| Ollama Client    | 원격 Gemma4 호출·재시도·keep-alive        | `requests` + `tenacity`                |
| GUI Driver       | 컨트롤 enumerate/조작/스크린샷            | `pywinauto` UIA + `uiautomation`       |
| XML Patcher      | `.mtproject` read/write/백업              | `e2e_explorer/xml_utils.py` (lxml)     |
| Knowledge Base   | 컨트롤·워크플로우·실패 누적               | SQLite + JSONL                         |
| Sandbox          | 사이클별 클린 복구                        | Hyper-V Checkpoint                     |
| Validator        | `.exp` 구조 검증·골든 비교                | `e2e_explorer/exp_validator.py` + lxml |
| Observer         | 액션 전후 `.mtproject`/`.exp` 스냅샷 캡처 | `e2e_explorer/observer.py`             |
| Pattern Extract  | observations → 일반화 규칙 후보(LLM)      | `e2e_explorer/pattern_extractor.py`    |
| mtproject Writer | 목표 → `.mtproject` XML 직접 합성         | `e2e_explorer/mtproject_writer.py`     |
| exp Writer       | 목표/XML → `.exp` 직접 합성               | `e2e_explorer/exp_writer.py`           |
| Round-trip XML   | 합성 XML을 MultiTool로 정규화·diff        | `e2e_explorer/roundtrip_xml.py`        |
| Round-trip exp   | 동일 상태에서 Export 후 의미적 diff       | `e2e_explorer/roundtrip_exp.py`        |
| Curriculum       | 학습 난이도·진도 관리                     | `e2e_explorer/curriculum.py`           |
| Claude routine   | 주간 감독·스킬 개선·hints 갱신            | `schedule` 스킬 cron (09:00)           |
| Policy           | 자동 승인/큐 적재 판정 기준               | `auto_approve_policy.md`               |
| Feedback Ch.     | Claude → Gemma 방향 지시 채널             | `next_night_hints.json`                |

### KB 스키마

| 저장소                          | 키 필드                                       | 용도                                                    |
| ------------------------------- | --------------------------------------------- | ------------------------------------------------------- |
| `kb/controls.sqlite`            | path, AutomationId, label, action             | 컨트롤 동작 사전                                        |
| `kb/workflows.jsonl`            | goal, action_seq, verified, source            | 검증된 시퀀스 (Gemma=`unverified`, Claude routine=승급) |
| `kb/xml_deltas/`                | before/after diff                             | GUI→XML 매핑 학습                                       |
| `kb/failures.jsonl`             | action, error, screenshot                     | 회귀 방지                                               |
| `kb/metrics.jsonl`              | date, coverage, pass_rate, hitl               | 자율도 일자별 지표 (Sunset 판정 근거)                   |
| `kb/observations/<id>/`         | before/after `.mtproject`+`.exp`, action.json | 4단계 학습 원천 데이터                                  |
| `kb/patterns/xml_rules.jsonl`   | rule, coverage, confidence                    | 액션 → XML delta 일반화 규칙 (승급된 것만)              |
| `kb/patterns/exp_rules.jsonl`   | rule, coverage, confidence                    | XML state → `.exp` 일반화 규칙 (승급된 것만)            |
| `kb/patterns/_candidates.jsonl` | rule, source_obs_ids                          | Gemma 추론 후보 (Claude routine 검증 대기)              |
| `kb/synthesis_failures.jsonl`   | goal, predicted, actual, diff                 | 합성 실패 케이스 — Claude routine 학습 입력             |

### 자기주도 루프 (야간 — Gemma4)

```python
while time in 00:00~05:30:
    obs   = ui_tree_dump() + mtproject_xml()
    hints = load("skills/e2e_explorer/next_night_hints.json")
    plan  = gemma4.plan(obs, kb, hints, goal)   # reasoning + JSON 출력
    act   = plan.next_action                     # click/type/save/export/patch
    res   = execute(act); diff = capture_diff()
    kb.record(act, res, diff)
    if produced_exp(res):
        if self_validate(res.path):              # exp_validator + 골든 diff + 합리성
            kb.add_candidate(verified=False)     # Gemma는 candidate만, 승급은 주간
        else:
            kb.record_failure()
```

**규칙**: Gemma4는 `verified=true` 직접 작성 금지. 모든 후보는 `kb/workflows.jsonl`에 `verified=false` + `source="nightly_<date>"`로 적재. 승급 권한은 주간 Claude routine.

목표 2단계 — Phase A(탐색·매핑) → Phase B(검증 워크플로우로 `.exp` 생성). Phase B 진입 조건: 해당 워크플로우가 Claude routine 또는 사용자 검토에서 `verified=true` 승급된 경우만.

### 학습 프로토콜 (4단계 Round-Trip)

MultiTool을 정답 오라클로 삼는 round-trip 학습. 격리 테스트 프로젝트 `MultiToolProject/E2EProject/`에서만 수행한다.

| 단계 | 명칭              | 동작                                                                             | 산출 KB                                   |
| ---- | ----------------- | -------------------------------------------------------------------------------- | ----------------------------------------- |
| 1    | 관찰 (GUI → XML)  | 액션 전후 `.mtproject` 스냅샷 → diff 추출                                        | `kb/observations/<id>/{before,after}.xml` |
| 2    | 관찰 (XML → .exp) | `.mtproject` 상태별 System Export → `.exp` 출력 캡처                             | `kb/observations/<id>/{before,after}.exp` |
| 3    | 합성·검증 (XML)   | `mtproject_writer`로 직접 XML 작성 → MultiTool open/save → 의미적 diff 0 검증    | `synthesis_accuracy_xml`                  |
| 4    | 합성·검증 (.exp)  | `exp_writer`로 직접 `.exp` 작성 → 동일 XML 상태에서 Export 후 의미적 diff 0 검증 | `synthesis_accuracy_exp`                  |

#### 의미적 diff 규칙

- XML: lxml `canonicalize`로 속성 순서·공백 정규화 후 비교. GUID·타임스탬프 등 휘발성 필드는 KB에 등록된 정규화 마스크 적용.
- `.exp`: `(*START - Implicit variables, made by EPEC Parser*)` 마커 이후 블록은 **합성 대상에서 제외 + diff 시도에서 무시**. `(* @PATH ... *)` 메타플래그는 정규화하여 비교.

#### 원자 액션 규율

복합 GUI 시퀀스는 학습 불가 — 항상 단일 의미 단위로 분해 실행. 분해 불가 액션 발견 시 `kb/failures.jsonl`에 `reason="non_atomic"`으로 적재 후 백트래킹.

#### 커리큘럼

학습은 단순→복합 순서로 진행. 레벨 정의·승급 기준은 W2 작업에서 확정.

#### 패턴 추출 흐름

야간: Gemma4가 신규 observations에 대해 일반화 규칙 후보를 LLM 추론으로 작성 → `kb/patterns/_candidates.jsonl`.
주간: Claude routine이 후보를 회귀 테스트(`exp_pairs` 보유 데이터로 검증) → 통과 시 `kb/patterns/xml_rules.jsonl` 또는 `exp_rules.jsonl`로 승급.

### 주간 Claude routine

```text
schedule cron: "0 9 * * *"
prompt:        /review-last-night
대상 디렉토리: logs/e2e/<어제날짜>/
```

| 처리 단계 | 동작                                                                                                      |
| --------- | --------------------------------------------------------------------------------------------------------- |
| 1. 입력   | `logs/e2e/<date>/summary.md` + `stats.json` + `metrics.json` + `failures.jsonl` + `candidates.jsonl` 읽기 |
| 2. 분류   | `auto_approve_policy.md` 기준으로 변경 위험도(낮음/중간/높음) 자동 판정                                   |
| 3. 자동   | 낮음: 즉시 `e2e/auto/<date>` 브랜치 commit (prompts 보강·KB 승급·failure 패턴 추가)                       |
| 4. 큐     | 중간/높음: `logs/e2e/<date>/review_queue.jsonl`에 적재 (사용자 차주 검토)                                 |
| 5. hints  | `skills/e2e_explorer/next_night_hints.json` 갱신 — 다음 야간 focus/avoid/promote 지시                     |
| 6. 기록   | `docs/tasks/<date>_e2e-review.md` 4항목 task 파일 자동 작성                                               |
| 7. Sunset | `kb/metrics.jsonl` 최근 3일 임계 충족 시 W6 트리거 (cron 자기 비활성화 + sunset 기록)                     |

### 자동 승인 매트릭스 (auto_approve_policy 요지)

| 변경 유형                                                             | 위험도 | 처리             |
| --------------------------------------------------------------------- | ------ | ---------------- |
| `unverified` → `verified` (3사이클 연속 자기검증 통과)                | 낮음   | 자동 승급        |
| `skills/e2e_explorer/prompts/*.md` 보강 추가                          | 낮음   | 자동 commit      |
| `kb/failures.jsonl` 패턴 → `e2e_explorer/xml_utils.py` primitive 추가 | 중간   | 자동 commit + PR |
| `skills/multitool/SKILL.md` 타이밍 규칙 추가                          | 중간   | 자동 commit + PR |
| 기존 SKILL 규칙 **삭제·반전**                                         | 높음   | 큐 적재          |
| `docs/exp_patterns/` 골든 교체                                        | 높음   | 큐 적재          |
| MultiTool 프로젝트 파일 수정                                          | 금지   | 거부 + 알림      |

### 자율도 지표 & Sunset 조건

매일 야간 사이클 종료 시 `logs/e2e/<date>/metrics.json` + `kb/metrics.jsonl`에 자동 기록. 09:00 Claude routine이 임계 충족 여부를 판정한다.

| 지표                       | 의미                                                                 | Sunset 임계         |
| -------------------------- | -------------------------------------------------------------------- | ------------------- |
| `feature_coverage`         | MultiTool 기능 중 skill 제어 가능 비율                               | 100%                |
| `exp_generation_pass_rate` | 시도 `.exp` 중 골든 의미적 diff 0 비율                               | ≥ 95% × 3일 연속    |
| `self_validate_pass_rate`  | 야간 자기검증 통과율                                                 | ≥ 95% × 3일 연속    |
| `hitl_queue_rate`          | 사람/Claude 개입 필요 건수 (사이클당)                                | ≤ 1건 × 3일 연속    |
| `regression_count`         | 자동 승급 후 재발 실패 건수                                          | 0건 × 3일 연속      |
| `synthesis_accuracy_xml`   | 직접 작성한 `.mtproject`가 MultiTool open/save 후 의미적 diff 0 비율 | **100% × 7일 연속** |
| `synthesis_accuracy_exp`   | 직접 작성한 `.exp`가 MultiTool Export와 의미적 diff 0 비율           | **100% × 7일 연속** |

→ 5개 지표 동시 충족 시 W6 자동 트리거 (Claude routine 자기 비활성화).

### 마일스톤

| 주차 | 상태 | 작업                                                                                                                                                          |
| ---- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 사전 | 완료 | Mac mini Ollama 원격 노출 (Tailscale)                                                                                                                         |
| 사전 | 완료 | `gemma4:26b` 헬스체크 200 OK 확인                                                                                                                             |
| 사전 | 완료 | 추론 ping 테스트 (PONG, 32 tok/s)                                                                                                                             |
| 사전 | 완료 | reasoning 응답 구조 확인 (`content`/`thinking`)                                                                                                               |
| W1   | 대기 | `skills/e2e_explorer/ollama_client.py` (JSON 강제·재시도·keep-alive)                                                                                          |
| W1   | 대기 | `pywinauto`로 MultiTool 컨트롤 트리 dump → JSON 저장                                                                                                          |
| W1   | 대기 | Gemma4에 트리 JSON 전송 → 최상위 메뉴 분류 PoC                                                                                                                |
| W2   | 대기 | KB 스키마 SQLite 생성 + Device 추가 후보 워크플로우 수동 시연 기록                                                                                            |
| W2   | 대기 | XML diff 캡처 → `kb/xml_deltas/` 자동 적재                                                                                                                    |
| W2.5 | 대기 | `observer.py` 구현 + `MultiToolProject/E2EProject/`에서 액션 10건 관찰 페어 누적                                                                              |
| W2.5 | 대기 | 의미적 diff 모듈 (`xml_canonicalize`, `exp_normalize` — Implicit 블록 제외)                                                                                   |
| W3   | 대기 | LangGraph FSM 루프 + 액션 timeout/백트래킹                                                                                                                    |
| W3   | 대기 | 야간 1시간 dry-run + `candidates.jsonl` 생성                                                                                                                  |
| W3   | 대기 | `auto_approve_policy.md` 작성 + `/review-last-night` 슬래시 커맨드 작성                                                                                       |
| W3   | 대기 | `schedule` 스킬로 09:00 cron 등록 (`e2e-morning-review`)                                                                                                      |
| W3.5 | 대기 | `pattern_extractor.py` (Gemma 후보 생성) + Claude routine 검증·승급 흐름 구현                                                                                 |
| W4   | 대기 | Task Scheduler 00:00 트리거 + 05:30 강제종료 + `-WakeToRun`·`-RestartCount`                                                                                   |
| W4   | 대기 | Hyper-V 스냅샷 자동 복구 스크립트 (`Checkpoint-VM`/`Restore-VMCheckpoint`)                                                                                    |
| W4   | 대기 | `next_night_hints.json` 양방향 채널 구현 (Claude 갱신 → orchestrator 주입)                                                                                    |
| W4   | 대기 | 워치독 (30분 무진전 시 재시작)                                                                                                                                |
| W5   | 대기 | `.exp` 자동 생성·검증·골든 비교 파이프라인                                                                                                                    |
| W5   | 대기 | Claude routine 자동 승급 1건 + 자동 PR 워크플로우                                                                                                             |
| W5.5 | 대기 | `mtproject_writer.py` + `roundtrip_xml.py` — XML 합성 후 MultiTool open/save → 의미적 diff 0 1건 통과                                                         |
| W5.5 | 대기 | `exp_writer.py` + `roundtrip_exp.py` — `.exp` 합성 후 Export 비교 → 의미적 diff 0 1건 통과                                                                    |
| W5.5 | 대기 | `curriculum.py` — 단순→복합 학습 진도 추적, 합성 정확도 일자별 기록                                                                                           |
| W5+  | 대기 | 워크플로우 KB 확장 (CAN·OD·J1939·Heartbeat 등 전 기능)                                                                                                        |
| W6   | 대기 | Sunset 지표 충족 시 09:00 cron 비활성화(`/schedule remove e2e-morning-review`) + skill 단독 운영 전환 + `docs/MultiTool_E2E_sunset.md` 기록                   |
| W7   | 대기 | MultiTool/스키마/CHM 버전 변경 자동 감지 → Sunset 해제 + delta 재학습 (`env_fingerprint.py`·`delta_classifier.py`·`version_migrator.py`·`relearn_trigger.py`) |

### 버전 변경 자동 재학습 (W7)

Sunset 후에도 MultiTool 또는 산출물 포맷이 바뀌면 학습 패턴이 무효화될 수 있다. 매 야간 사이클 시작 시 환경 핑거프린트를 비교하여 변경 감지 → 변경 정도에 따라 자동 재학습 모드 결정.

| 핑거프린트 대상     | 수집 방법                                          |
| ------------------- | -------------------------------------------------- |
| MultiTool 버전      | `(Get-Item MultiTool.exe).VersionInfo.FileVersion` |
| `.mtproject` 스키마 | XML root의 SDK·schema 버전 속성                    |
| `.exp` 포맷         | `(* @PATH ... *)` 헤더 + EPEC Parser 마커 정규식   |
| `Manual.chm` 해시   | SHA256                                             |
| UI 트리 구조        | `kb/controls.sqlite`와 의미적 diff                 |

변경 분류 → 재학습 모드:

| 변경 유형                  | 재학습 범위                               |
| -------------------------- | ----------------------------------------- |
| 패치(8.4.1→8.4.2) UI만     | 컨트롤 트리 갱신 (패턴 보존)              |
| Manual.chm만 변경          | 신규 기능 메뉴 탐색만                     |
| `.mtproject` 노드 1개 추가 | 해당 XPath 시퀀스만 재학습                |
| 메이저 버전 (8.4→8.5)      | 전체 재학습 + 기존 패턴 마이그레이션 후보 |

버전별 KB 격리:

```text
kb/
  versions/
    8.4/patterns/
    8.5/patterns/           ← 진입 시 8.4 복사 후 회귀 테스트
  shared/observations/      ← 버전 무관 관찰 데이터
```

### 디렉토리 예정 구조

```text
skills/e2e_explorer/
  SKILL.md
  orchestrator.py
  ollama_client.py
  ui_driver.py
  xml_utils.py                   ← .mtproject canonicalize·정규화
  exp_validator.py               ← .exp 파싱·Implicit 블록 제외 normalize
  observer.py                    ← 액션 전후 .mtproject/.exp 스냅샷 캡처
  pattern_extractor.py           ← observations → 후보 규칙 (Gemma LLM 추론)
  mtproject_writer.py            ← 목표 → .mtproject XML 직접 합성
  exp_writer.py                  ← 목표/XML → .exp 직접 합성
  roundtrip_xml.py               ← 합성 XML → MultiTool open/save → diff
  roundtrip_exp.py               ← 합성 .exp → Export 결과 diff
  curriculum.py                  ← 학습 난이도·진도 관리
  kb_store.py
  next_night_hints.json          ← Claude routine이 매일 09:00 갱신
  auto_approve_policy.md         ← 자동 승인 매트릭스 기준
  prompts/                       ← Gemma용 시스템 프롬프트
    orchestrator.md
    plan.md
    self_validate.md
    extract_pattern.md           ← Gemma 패턴 후보 추출용
  kb/
    controls.sqlite
    workflows.jsonl
    failures.jsonl
    metrics.jsonl                ← 자율도 누적 지표
    synthesis_failures.jsonl     ← 합성 실패 케이스
    xml_deltas/
    observations/                ← 4단계 학습 원천 데이터 (per-action 디렉토리)
      <id>/before.xml
      <id>/after.xml
      <id>/before.exp
      <id>/after.exp
      <id>/action.json
    patterns/
      xml_rules.jsonl            ← 승급된 XML 규칙
      exp_rules.jsonl            ← 승급된 .exp 규칙
      _candidates.jsonl          ← Gemma 후보 (Claude routine 검증 대기)
  scripts/
    nightly_run.ps1
    register_task.ps1            ← Task Scheduler 등록
    snapshot_restore.ps1
    watchdog.ps1
MultiToolProject/
  E2EProject/                    ← 학습·검증 격리 작업장 (모든 round-trip 여기서 수행)
  ...                            ← 그 외 실제 프로젝트는 학습 대상 아님
logs/e2e/<YYYY-MM-DD>/
  summary.md                     ← Gemma가 작성한 야간 보고 (성공 워크플로우 포함)
  stats.json
  metrics.json                   ← 일자별 자율도 지표 스냅샷
  candidates.jsonl               ← unverified 후보 워크플로우
  successes.jsonl                ← 성공 액션 로그
  failures.jsonl                 ← 실패 액션 로그
  prompts_used.jsonl
  exp_outputs/
  screenshots/
  review_queue.jsonl             ← Claude가 자동처리 못한 항목
.claude/commands/
  review-last-night.md           ← Claude routine 진입 슬래시
docs/
  MultiTool_E2E.md               ← 본 문서
  MultiTool_E2E_sunset.md        ← W6 트리거 시 자동 생성 (종료 기록)
  tasks/
    2026-05-14_e2e-w1-poc.md
    <date>_e2e-review.md         ← Claude routine이 매일 작성
```

### 안전장치

| 위험                      | 대응                                                                                |
| ------------------------- | ----------------------------------------------------------------------------------- |
| `.mtproject` 손상         | 액션 전 백업 + 사이클당 VM 스냅샷                                                   |
| 무한루프                  | 액션 timeout + 동일액션 N회 시 백트래킹                                             |
| 환각 워크플로우           | Gemma는 `unverified`만 생성, `verified` 승급은 Claude routine + auto_approve_policy |
| Claude routine 폭주       | `e2e/auto/<date>` 브랜치 강제, 일일 변경 라인수 상한, 사이클당 1회만 cron 실행      |
| 네트워크 끊김             | `tenacity` 지수 백오프 + 30분 헬스체크                                              |
| Mac mini sleep            | `caffeinate` 상시                                                                   |
| 모델 언로드               | `keep_alive: "8h"` 강제                                                             |
| Windows 절전·종료         | Task에 `-WakeToRun -AllowStartIfOnBatteries -StartWhenAvailable`                    |
| GUI 잠금 (pywinauto 실패) | 자동로그인 + 잠금 해제 유지, 또는 Hyper-V VM 안에서 console session 유지            |
| 사용자 로그오프           | Task "사용자 로그온 여부와 관계없이 실행" + VM 권장                                 |
| 09:00 routine 실패        | `schedule` 자동 재시도 + 3회 연속 실패 시 일시정지 + 알림                           |
| 진전 정체                 | 3사이클 연속 신규 컨트롤 0건 → 자동 일시정지 + 로그 기록                            |

## Diff

(완료 후 기록) commit hash + 금지조건 준수 ✓ + 검증조건 통과 결과

## 참조

| 문서                                                             | 내용                          |
| ---------------------------------------------------------------- | ----------------------------- |
| [PROJECT.md](PROJECT.md)                                         | 프로젝트 정의서               |
| [../skills/e2e_explorer/](../skills/e2e_explorer/)               | 통합 E2E 스킬 (W1+ 작성 예정) |
| [exp_patterns/](exp_patterns/)                                   | `.exp` 골든·매핑 참조 자산    |
| [versions/8.4/function_map.json](versions/8.4/function_map.json) | 49개 기능 사전 (탐색 시드)    |
