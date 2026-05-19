# Morning Review — 2026-05-19

## 핵심 지표 비교

| 지표               | 이전 baseline | 새 baseline | 변화   |
| ------------------ | ------------- | ----------- | ------ |
| 총 시도            | 395.0         | 153.0       | -242.0 |
| 성공               | 149.0         | 72.0        | -77.0  |
| 실패               | 246.0         | 81.0        | -165.0 |
| 평균 value_changes | 22.0          | 22.5        | +0.5   |

## 이전 baseline 시드별 의도 변경 (Intent)

set intersection - noise(≥50% 공통)으로 추출:

| 시드                | 추출된 의도 변경                                   |
| ------------------- | -------------------------------------------------- |
| diag_cycle_min      | `IsCondition: false→true`                          |
| diag_ref5v_min      | `IsCondition: false→true`                          |
| diag_temp_min       | `IsCondition: true→false`                          |
| diag_voltage_min    | `IsCondition: true→false`                          |
| od_add_index        | `CobId: 0→185`, `CobId: 181→185`, `CobId: 281→185` |
| od_add_subindex     | `CobId: 0→185`, `CobId: 181→185`, `CobId: 281→185` |
| od_restore_settings | `CobId: 0→185`, `CobId: 181→185`, `CobId: 281→185` |
| pdo_add_rx          | `CobId: 0→185`, `CobId: 181→185`, `CobId: 281→185` |
| pdo_add_tx          | `CobId: 0→185`, `CobId: 181→185`, `CobId: 281→185` |
| pdo_variable_remove | `CobId: 0→185`, `CobId: 181→185`, `CobId: 281→185` |

## 결론

⚠ 위 두 라운드는 모두 **baseline 정합화 적용 전** 데이터. "current"는 새 baseline 미적용 폴더의 partial run 데이터로 비교 가치 제한적.

**진짜 baseline 정합화 검증** (dryrun_one_seed.py — application_node_id 단독):

| 지표                    | 이전 baseline | clean_baseline (dryrun)        |
| ----------------------- | ------------- | ------------------------------ |
| mt_size_delta           | +14,293       | **0**                          |
| value_changes           | 28            | **3**                          |
| 노이즈 (의미 없는 변경) | 27            | **0**                          |
| signal                  | 1             | 3 (NodeId 7→5, CobId × 2 파급) |

→ 노이즈 28건 중 27건 제거, 남은 3건은 모두 의도 + SDO base+NodeId 자연 파급.

## C 카테고리 dry 분석 (재검증 ★★ 작업)

이전 archive의 `diag_*_min`/`*_max` 시드 추출 intent = **`IsCondition` 체크박스 토글** (Minimum/Maximum 값 아님).

원인: `set_field_auto`가 `table_column` 인자를 무시하던 시점 → "Temperature" 라벨 우측 인접 체크박스 클릭 → IsCondition 토글만 발생.

**현재 상태**: commit `16b2b6c`로 fix 완료 (table_column → `click_table_cell` 경유). 다음 야간 사이클에서 진짜 Minimum/Maximum 값 변경이 일어나는지 검증 필요. 코드 측 작업은 완료.

## 다음 작업 권고

1. ★★★ 야간 사이클 재실행 — clean_baseline + io_pin recipe + table_column fix 통합 검증 (3~4h)
2. 결과 `results.jsonl` 다시 `night_ui_review.py`로 분석 → 진짜 post-fix 지표 확보
