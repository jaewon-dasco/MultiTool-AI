# Morning Review — 2026-05-19

## 핵심 지표 비교

| 지표 | 이전 baseline | 새 baseline | 변화 |
| ---- | ------------- | ----------- | ---- |
| 총 시도 | 879.0 | 105.0 | -774.0 |
| 성공 | 454.0 | 71.0 | -383.0 |
| 실패 | 425.0 | 34.0 | -391.0 |
| 평균 value_changes | 11.1 | 0.6 | -10.4 |

## 이전 baseline 시드별 의도 변경 (Intent)

set intersection - noise(≥50% 공통)으로 추출:

| 시드 | 추출된 의도 변경 |
| ---- | ---------------- |
| application_node_id | `NodeId: 7→5` |
| codesys_node_id | `CodesysNodeId: 1→5` |
| diag_cycle_max | `BitRate: 125→250`, `Bitrate: 125→250`, `CobId: 181→0` |
| diag_cycle_min | `BitRate: 125→250`, `Bitrate: 125→250`, `CobId: 181→0` |
| diag_ref5v_max | `BitRate: 125→250`, `Bitrate: 125→250`, `CobId: 181→0` |
| diag_temp_max | `BitRate: 125→250`, `Bitrate: 125→250`, `CobId: 181→0` |
| diag_voltage_max | `BitRate: 125→250`, `Bitrate: 125→250`, `CobId: 181→0` |
| io_pin1_10_var_name | `Variable: X1_10→TEST_PIN1_10` |
| io_pin1_11_var_name | `Variable: X1_11→TEST_PIN1_11` |
| io_pin1_12_var_name | `Variable: X1_12→TEST_PIN1_12` |
| io_pin1_2_var_name | `Variable: VAVLE_UP→TEST_PIN1_2` |
| io_pin1_3_var_name | `Variable: VAVLE_DN→TEST_PIN1_3` |
| io_pin1_7_var_name | `Variable: LED1→TEST_PIN1_7` |
| io_pin1_8_var_name | `Variable: LED2→TEST_PIN1_8` |
| io_pin1_9_var_name | `Variable: X1_9→TEST_PIN1_9` |
| monitoring_start_interval | `StartInterval: 1000→2000` |

## 결론
- 노이즈 (모든 시드 공통 변경): 0건 → 0건
- 평균 value_changes: 11.1 → 0.6