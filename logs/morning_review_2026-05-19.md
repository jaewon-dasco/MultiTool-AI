# Morning Review — 2026-05-19

## 핵심 지표 비교

| 지표               | 이전 baseline | 새 baseline | 변화   |
| ------------------ | ------------- | ----------- | ------ |
| 총 시도            | 573.0         | 153.0       | -420.0 |
| 성공               | 244.0         | 99.0        | -145.0 |
| 실패               | 329.0         | 54.0        | -275.0 |
| 평균 value_changes | 20.1          | 0.5         | -19.6  |

## 이전 baseline 시드별 의도 변경 (Intent)

set intersection - noise(≥50% 공통)으로 추출:

| 시드             | 추출된 의도 변경          |
| ---------------- | ------------------------- |
| diag_cycle_min   | `IsCondition: false→true` |
| diag_ref5v_min   | `IsCondition: false→true` |
| diag_temp_min    | `IsCondition: true→false` |
| diag_voltage_min | `IsCondition: true→false` |

## 결론

✅ **Baseline 정합화 + 신규 핸들러 통합 성공**:

| 지표                     | 이전 baseline | 현재 라운드 | 변화  |
| ------------------------ | ------------- | ----------- | ----- |
| 노이즈 (≥50% 공통 변경)  | 18건          | **0건**     | -100% |
| 평균 value_changes       | 20.1          | **0.5**     | -97%  |
| Intent 추출 가능 시드 수 | 4             | **13**      | +225% |
| OK 비율                  | 43%           | **65%**     | +22pp |

## 카테고리별 회복

| 카테고리        | 이전 archive | 현재 라운드 | 비고                                               |
| --------------- | ------------ | ----------- | -------------------------------------------------- |
| B (CAN)         | 24/24        | **24/24**   | 유지                                               |
| C (Diagnostics) | 24/24        | **0/24**    | ✗ 회귀 — table_column fix 후 click_table_cell 실패 |
| A (Network)     | 6/18         | 9/18        | +3 (net_bitrate_change 0→3 회복)                   |
| D (OD)          | 9/24         | 9/24        | 유지 (dialog 자동화 미구현)                        |
| E (PDO)         | 9/15         | 9/15        | 유지                                               |
| F (I/O)         | 0/48         | **48/48**   | ✅ 신규 회복 (io_mode + io_var_name 둘 다 완벽)     |

## 새 핸들러 검증 (실 야간 결과)

- `network_property` (net_bitrate_change × 3 cycle): **3/3 ✓** vc=3 (NETWORK1 Bitrate 250→500 + connected device 2개 BitRate 동기화 파급)
- `io_pin_recipe.set_pin_mode` (8 핀 × 3 cycle): **24/24 ✓**
- `io_pin_recipe.set_pin_variable_name` (8 핀 × 3 cycle): **24/24 ✓**

## C 카테고리 회귀 분석 (★★ 다음 작업)

이전 archive에서 추출된 intent: `IsCondition: true↔false` (체크박스 토글) — 이건 잘못된 컨트롤 조작이었음을 morning_review 2026-05-19 dry 분석에서 확인.

commit `16b2b6c`로 `table_column` 인자를 `click_table_cell`로 라우팅하도록 fix했으나, **현재 라운드에서 C 24/24 모두 `ui_change_failed`**. `click_table_cell`이 Diagnostics 테이블에서 row_marker(Temperature/SupplyVoltage/...)나 col_marker(Minimum/Maximum)를 못 찾는 듯.

다음 액션: Diagnostics 탭 probe → `find_label("Temperature")` / `find_label("Minimum")` 가시성 검증 → `click_table_cell` 보정.

## 다음 작업 권고

1. ★★ C 카테고리 회귀 디버그 — probe_diagnostics.py 작성, click_table_cell 보정
2. ★★ D OD dialog (od_remove/store/restore/import/export 15/24 회복)
3. ★★ A toolbar_action_with_dialog (net_add_device/slave 9/18 회복)
4. ★ E PDO pdo_remove_tx/rx 6/15 회복
