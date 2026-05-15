# E2E UI→XML 매핑 학습 세션 #1

| 항목   | 값                                     |
| ------ | -------------------------------------- |
| 작성일 | 2026-05-15                             |
| 상태   | 완료 (4 step + baseline, KB 9건)       |
| 방식   | 사용자 수동 UI 조작 + Claude diff 분석 |
| Commit | —                                      |

## 완료조건
사용자가 정의한 15+ step UI 조작 시나리오를 1 세션으로 완주하고 각 step의 UI 액션 ↔ XML diff 매핑을 `learning_log.md`에 누적해 KB 후보 패턴 5건 이상 추출.

## 금지조건
- 자동 UI 클릭 (이번 세션은 매핑 학습 전용, 자동화는 다음 phase)
- 중간 step에서 .mtproject 임의 수정 (사용자 UI 조작만)
- 세션 도중 baseline 변경

## 검증조건
- 각 step 후 `.mtproject` + `.exp` sha256 변화 기록
- diff에서 의도적 변경(value)과 부수효과(Guid 재생성·BOM·PDO 변경 등) 분리
- 최종 `learning_log.md`에 step별 표 + xpath 매핑 표 생성

## 시나리오 사양

### 시작 상태
- `DasDemoProject.mtproject` 빈 상태 (기존 CU_3606_21_1·2 제거 후)
- 단일 baseline에서 누적 변경

### Step 1: 디바이스 5개 추가

| 모델     | 역할     | CODESYS |
| -------- | -------- | ------- |
| 5050-82  | 컨트롤러 | 2.3     |
| 3720-21  | 컨트롤러 | 2.3     |
| 3606-21  | 컨트롤러 | 2.3     |
| 3724-01  | 컨트롤러 | 2.3     |
| 6807-220 | 모니터   | 3.5     |

### Step 2: 네트워크 3개 구성

| 네트워크 | 연결 디바이스·CAN           |
| -------- | --------------------------- |
| NETWORK1 | 5050-82.CAN1, 3720-21.CAN1  |
| NETWORK2 | 5050-82.CAN2, 3606-21.CAN1  |
| NETWORK3 | 5050-82.CAN3, 6807-220.CAN1 |
| (단독)   | 3724-01                     |

### Step 3: BitRate 설정

| 대상     | BitRate                |
| -------- | ---------------------- |
| NETWORK1 | 250 kbit/s             |
| NETWORK2 | 500 kbit/s             |
| NETWORK3 | 1000 kbit/s            |
| 3724-01  | 250 kbit/s (단독 모드) |

### Step 4: 나머지 default 유지, .exp 생성 + 저장

## 워크플로

```
ui_learn.py --init mapping_session_1   ← baseline 캡처
[사용자: 디바이스 1개 추가 + 저장]
ui_learn.py --capture "add 5050-82 CDS2.3"   ← step1 diff
[사용자: 다음 디바이스 추가 + 저장]
ui_learn.py --capture "add 3720-21 CDS2.3"   ← step2 diff
... (각 step 반복)
ui_learn.py --report                          ← learning_log.md 생성
```

## Diff
**Commit**: 미커밋

**금지조건 준수**: TBD

**검증 결과**: TBD
