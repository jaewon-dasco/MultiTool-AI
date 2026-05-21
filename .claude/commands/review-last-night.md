---
description: 어젯밤 E2E 야간 사이클 결과 자동 검토. 로컬 logs 분석 + 패턴 추출 후보 작성 + commit.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

어젯밤(또는 가장 최근) E2E 야간 사이클의 산출물을 검토하고 다음 작업을 수행한다. 절대 사용자에게 질문하지 말고 끝까지 자동 진행.

## 1. 사이클 폴더 식별

```bash
ls -td logs/e2e/2026-* 2>/dev/null | head -1
```

찾지 못하면 "no overnight cycle found"를 출력하고 종료.

## 2. 검토 대상

| 파일                              | 역할                              |
| --------------------------------- | --------------------------------- |
| `summary.md`                      | 사이클 통계                       |
| `observations.jsonl`              | Qwen3.5 관찰 응답 누적            |
| `sequences/<seq_id>/summary.json` | 각 시퀀스 step 트레이스           |
| `snapshots/`                      | `.mtproject`·`.exp` 스냅샷 파일들 |

## 3. 분석 항목

각 시퀀스(`can1_bitrate`, `can1_nodeid`, `can1_heartbeat`, `can1_buffering`, `can1_j1939`)에 대해:

1. **결정성**: 같은 transition을 반복했을 때 `.mtproject` sha256이 동일한가
2. **.exp 영향**: XML 변경이 `.exp` 파일을 변화시켰는가 (sha256 비교)
3. **Qwen3.5 응답 일관성**: 동일 시퀀스의 N회 응답 중 핵심 패턴 식별
4. **실패율**: errors 필드 합계

## 4. 산출물 (자동 작성)

`logs/e2e/<date>/morning_review.md` 작성 — 5섹션:

```markdown
# E2E 야간 검토 — <date>

## 통계
- 사이클: N · 시퀀스 실행: N · transition: N · 실패: N

## 결정성 검증
- can1_bitrate: ✓/✗ (250→500 시그니처 sha256=...)
- ...

## .exp 영향
- can1_bitrate: .exp 변화 없음 (Export 트리거 없음 — 예상)
- ...

## Qwen3.5 관찰 요지
- 시퀀스별 핵심 표현 추출

## 다음 야간 제안 (next_night_hints 후보)
- focus_areas: [...]
- avoid: [...]
```

## 5. KB 후보 패턴 적재

분석에서 안전하게 확인된 결정적 transition은 `skills/e2e_explorer/kb/patterns/_candidates.jsonl`에 후보로 추가:

```jsonl
{"xpath": "/MtProject/Device[1]/CANs/CAN/BitRate", "rule": "text-only mutation, deterministic, .exp unchanged", "source": "morning_review_<date>", "confidence": "high", "verified": false}
```

## 6. Commit

```bash
cd D:\4_AIProject\4_CoDeSys\AI_MutiTool
git checkout -b e2e/auto/<date> 2>/dev/null || git checkout e2e/auto/<date>
git add logs/e2e/<date>/morning_review.md skills/e2e_explorer/kb/patterns/
git commit -m "chore(e2e): morning review <date> — N transitions analyzed"
git checkout master
```

(브랜치만 만들고 main/master에 머지하지 않음 — 사용자 검토 후 머지)

## 7. 종료 출력

```
E2E_MORNING_REVIEW done · cycle=<date> · cycles=N · transitions=N · candidates=N · branch=e2e/auto/<date>
```

이후 사용자에게 더 묻지 말고 즉시 종료.
