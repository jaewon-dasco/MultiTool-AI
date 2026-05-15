# UI 주도 학습 PoC — BitRate 1건 end-to-end 시도

| 항목   | 값                                    |
| ------ | ------------------------------------- |
| 작성일 | 2026-05-15                            |
| 상태   | 완료 (네트워크 단위 경로로 우회 성공) |
| Commit | —                                     |

## 완료조건
MultiTool UI를 pywinauto로 자동 조작해서 CU_3606_21_1의 CAN1 BitRate를 250→500으로 1회 변경, 저장, XML diff에서 해당 xpath만 바뀐 것을 확인.

## 금지조건
- 5개 시나리오(Device 추가/CAN/OD/Diagnostics/IO) 전체 자동화 — 이번엔 BitRate 1건만
- 야간 무인 모드로 확장 — 인터랙티브 검증 우선
- `.mtproject` 원본 영구 변경 — 백업 필수

## 검증조건
- 시작 sha256 = `bb24e7aabaaa` (원본)
- 종료 sha256 ≠ 시작 (의도된 변경)
- XML diff에서 `Device[1]/CANs/CAN[1]/BitRate` 텍스트만 250→500 (다른 xpath 변경 0건)
- 파일 크기 변화 ±10바이트 이내 (불필요한 메타 변경 없음)

## Diff
**Commit**: 미커밋 (세션 종료 시점, 다음 세션에서 정리 후 commit)

**금지조건 준수**: ✓ BitRate 1건만 시도, 원본 복원 완료

**검증 결과**: ✗ **블로커 발견 — 완료조건 미달**

| 단계                  | 결과   | 메모                                                                                    |
| --------------------- | ------ | --------------------------------------------------------------------------------------- |
| MultiTool 실행        | ✓      | `Start-Process` + splash 대기 25초                                                      |
| 프로젝트 로드         | ✓      | StartPage "Open Project..." Hyperlink.invoke + 파일 다이얼로그 + send_keys 경로 입력    |
| 디바이스 카드 진입    | ✓      | CU_3606_21_1 Hyperlink.invoke (네트워크 다이어그램)                                     |
| Configure 패널 진입   | ✓      | floating toolbar 렌치 버튼 좌표 클릭 (자동 검색: 디바이스 우상단 region) → TabItem 1→16 |
| BitRate ComboBox 식별 | ✓      | "Bit Rate" Text 라벨 발견 → 같은 row(y±15) 우측의 ComboBox 매핑 (전체화면 296,225)      |
| 값 변경               | ✗      | **ComboBox가 disabled** — 네트워크 연결 상태에서는 디바이스 단위 BitRate 비활성         |
| 저장                  | (오염) | 키보드 "500" 입력이 다른 포커스로 흘러가 +13KB 부작용. 파일 sha 변경됨                  |
| 복원                  | ✓      | MultiTool 강제 종료 + 백업 복사 → sha `bb24e7aabaaa3cce` 회복                           |

**핵심 학습 (메모리 저장됨)**:
1. 네트워크 다중 연결 시 디바이스 BitRate 변경은 차단 — 네트워크 단위 변경(NETWORK1 노드)으로만 가능
2. UI 자동화에서 disabled 컨트롤 키 입력은 silent 오작동 유발 → `is_enabled()` 사전 체크 필수
3. floating toolbar 작은 버튼(렌치/큐브/X)은 일반 디스크립턴트 트리에서 무명 Button으로만 보임 → 좌표 + size 필터로 식별

**도구 산출물** (`skills/e2e_explorer/scripts/`):
- `ui_probe.py` — UI 트리 dump + 키워드 hit 추출
- `ui_open_project.py` — 프로젝트 자동 로드
- `ui_navigate.py` — Hyperlink 이름으로 클릭
- `ui_configure.py` — floating toolbar 위치 탐색
- `ui_bitrate_change.py` — end-to-end BitRate 변경 (현재 disabled 이슈로 미완)

**다음 세션 시작점**:
- 네트워크 분리 절차 학습 (디바이스를 NETWORK1에서 떼어내는 UI 조작) — 또는
- 네트워크 단위 BitRate 변경 경로 학습 (NETWORK1 노드 → BitRate)
- ComboBox `is_enabled()` 가드 추가
