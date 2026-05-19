# E2E 자동화 작업 스케줄

작업 히스토리·진행 상태·남은 항목 추적용. 작업 시작/완료 시 본 파일을 갱신한다.

| 항목          | 값                                       |
| ------------- | ---------------------------------------- |
| 최근 갱신     | 2026-05-19                               |
| 현재 단계     | I/O recipe 완료, 야간 재실행 대기        |
| 마지막 commit | `dbc5312` 디바이스 템플릿 시드 자동 생성 |

## 진행 중

| #   | 작업   | 상태 | 비고                |
| --- | ------ | ---- | ------------------- |
| —   | (없음) | —    | 다음 항목 선택 대기 |

## 완료 (최근 → 과거)

| 일자       | 작업                                                 | Commit    |
| ---------- | ---------------------------------------------------- | --------- |
| 2026-05-19 | 디바이스 템플릿 XML 파서 + F_io.json 자동 생성       | `dbc5312` |
| 2026-05-19 | io_pin UIA recipe + WPF DataGrid 가이드 문서화       | `a8c8250` |
| 2026-05-19 | set_field_auto에 table_column 인자 추가              | `16b2b6c` |
| 2026-05-19 | restart 후 Open Project 자동화 추가                  | `f7fcabe` |
| 2026-05-19 | 야간 cycles 5→3 (재시작 페널티 반영)                 | `eb42eaa` |
| 2026-05-19 | per-seed MultiTool 재시작으로 baseline 노이즈 제거   | `3cfda60` |
| 2026-05-18 | IO/Network/OD 시드 확장 + 야간 framework 보완        | `1313b4a` |
| 2026-05-18 | night-UI framework + API portability                 | `23b2001` |
| 2026-05-17 | Phase 3 시드 65건 + marathon_status + morning_review | `71909ba` |
| 2026-05-16 | marathon mode (45h continuous) + Phase 2 시드        | `58b87eb` |

## 남은 작업

우선순위(★★★ 최상 ~ ★ 최하) → 관련도(앞 작업의 결과를 활용하는 흐름) 순으로 정렬.

| 우선 | 분류         | 작업                                                                                          | 영향                                 | 비용               |
| ---- | ------------ | --------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------ |
| ★★★  | 근본 개선    | Baseline 정합화 — MultiTool 로드 후 즉시 save한 깨끗한 .mtproject 백업 생성                   | Save 부수효과 28→0 (ML 가능)         | 30분               |
| ★★★  | 회복 검증    | 야간 사이클 재실행 — 새 io_pin recipe + 디바이스 템플릿 검증                                  | F 카테고리 0→8 회복 확인             | 3~4h 야간          |
| ★★★  | 회복 검증    | morning_review 실행 — 누적 results.jsonl에서 ML signal 추출                                   | C/B 노이즈 비교, 진짜 의도 변경 식별 | 30분               |
| ★★   | 디버그       | C 카테고리 재검증 — table_column fix 후 실제 Min/Max 값 변경 확인                             | "OK 24건"이 진짜 의도된 변경인지     | 1h                 |
| ★★   | 핸들러 구현  | `network_property` 핸들러 — NETWORK 노드 클릭 → BitRate 변경                                  | A: net_bitrate_change 0→3            | 2h                 |
| ★★   | 핸들러 구현  | `dialog_probe` → 실 핸들러 승격 — Pre-defined Index 자동화                                    | D: od_add_predefined 0→3             | 2h                 |
| ★★   | 디버그       | A 카테고리 `toolbar_action_with_dialog` 디버그 (net_add_device 0/3, net_add_slave_device 0/3) | A: 6→12 회복                         | 2h                 |
| ★★   | 디버그       | D 카테고리 OD dialog 처리 강화 (od_remove_first, od_store/restore/import/export)              | D: 9→24 회복                         | 3h                 |
| ★    | 디버그       | E 카테고리 PDO 일부 실패 (pdo_remove_tx/rx)                                                   | E: 9→15 회복                         | 1h                 |
| ★    | 미정 (probe) | Variable Name 변경 경로 탐색 (핀 우클릭/더블클릭 → 다이얼로그)                                | F: +8 시드 추가                      | 1h probe + 2h 구현 |
| ★    | 확장         | 다른 디바이스 시드(3720, 5050, 6807) 일반화                                                   | 디바이스별 ×8 시드                   | 1h × 3종           |

## 참조

- 운영 지침·알려진 함정·갱신 프로토콜: [skills/e2e_explorer/multitool_e2e.md](../skills/e2e_explorer/multitool_e2e.md)
- 프로젝트 정의: [docs/PROJECT.md](PROJECT.md)
- 작업 단위 task: [docs/tasks/](tasks/)
