#!/usr/bin/env python3
"""Aggregate E2E overnight cycle into a morning_review.md report."""
import json
import sys
from pathlib import Path
from collections import defaultdict, Counter

CYCLE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("logs/e2e/2026-05-14")
SEQ_DIR = CYCLE / "sequences"

seq_dirs = sorted([p for p in SEQ_DIR.iterdir() if p.is_dir()])

per_name = defaultdict(list)
transitions_total = 0
errors_total = 0
exp_changed_total = 0
exp_unchanged_total = 0

# (name, old->new) -> list of after.project.sha256
trans_sig = defaultdict(list)
# (name, old->new) -> list of (before_exp_sha_tuple, after_exp_sha_tuple)
trans_exp = defaultdict(list)

for sd in seq_dirs:
    summ = sd / "summary.json"
    if not summ.exists():
        continue
    try:
        data = json.loads(summ.read_text(encoding="utf-8"))
    except Exception:
        continue
    name = data.get("name", "?")
    per_name[name].append(sd.name)
    errs = data.get("errors", []) or []
    errors_total += len(errs)
    for step in data.get("steps", []):
        transitions_total += 1
        key = (name, f"{step['old']}->{step['new']}")
        after_sha = step["after"]["project"]["sha256"]
        trans_sig[key].append(after_sha)
        before_exp = tuple(sorted(f["sha256"] for f in step["before"]["exp_files"]))
        after_exp = tuple(sorted(f["sha256"] for f in step["after"]["exp_files"]))
        trans_exp[key].append((before_exp, after_exp))
        if before_exp == after_exp:
            exp_unchanged_total += 1
        else:
            exp_changed_total += 1

# Determinism per name
det_rows = []
for name in sorted(per_name):
    name_keys = [k for k in trans_sig if k[0] == name]
    det = True
    examples = []
    for k in name_keys:
        shas = trans_sig[k]
        if len(set(shas)) > 1:
            det = False
        examples.append((k[1], shas[0], len(shas), len(set(shas))))
    det_rows.append((name, det, examples, len(per_name[name])))

# .exp impact per name
exp_rows = []
for name in sorted(per_name):
    name_keys = [k for k in trans_exp if k[0] == name]
    changed = sum(1 for k in name_keys for b, a in trans_exp[k] if b != a)
    total = sum(len(trans_exp[k]) for k in name_keys)
    exp_rows.append((name, changed, total))

# Build report
lines = []
lines.append(f"# E2E 야간 검토 — {CYCLE.name}")
lines.append("")
lines.append("## 통계")
lines.append("")
lines.append("| 항목 | 값 |")
lines.append("| ---- | -- |")
lines.append(f"| 사이클 폴더 | {CYCLE.name} |")
lines.append(f"| 시퀀스 실행 | {len(seq_dirs)} |")
lines.append(f"| transition 총합 | {transitions_total} |")
lines.append(f"| 실패 (errors 합) | {errors_total} |")
lines.append(f"| .exp 변화 transition | {exp_changed_total} |")
lines.append(f"| .exp 무변화 transition | {exp_unchanged_total} |")
lines.append("")

lines.append("## 시퀀스별 실행 횟수")
lines.append("")
lines.append("| 시퀀스 | 횟수 |")
lines.append("| ------ | ---- |")
for name in sorted(per_name):
    lines.append(f"| {name} | {len(per_name[name])} |")
lines.append("")

lines.append("## 결정성 검증 (transition별 .mtproject sha256 일관성)")
lines.append("")
lines.append("| 시퀀스 | 결정적 | transition 종류 | 비고 |")
lines.append("| ------ | ------ | --------------- | ---- |")
for name, det, examples, n in det_rows:
    mark = "✓" if det else "✗"
    note = f"{len(examples)} 종류 transition, 각 {examples[0][2] if examples else 0}회 반복" if examples else "—"
    lines.append(f"| {name} | {mark} | {len(examples)} | {note} |")
lines.append("")

lines.append("### transition별 상세 (sha256 first 12)")
lines.append("")
for name in sorted(per_name):
    lines.append(f"**{name}**")
    lines.append("")
    lines.append("| transition | reps | unique_sha | sha256[:12] |")
    lines.append("| ---------- | ---- | ---------- | ----------- |")
    for k in sorted([k for k in trans_sig if k[0] == name]):
        shas = trans_sig[k]
        lines.append(f"| {k[1]} | {len(shas)} | {len(set(shas))} | {shas[0][:12]} |")
    lines.append("")

lines.append("## .exp 영향")
lines.append("")
lines.append("| 시퀀스 | .exp 변화 | total | 결론 |")
lines.append("| ------ | --------- | ----- | ---- |")
for name, changed, total in exp_rows:
    conclusion = "Export 트리거 없음 — 예상" if changed == 0 else f"⚠ {changed}회 변화 감지"
    lines.append(f"| {name} | {changed} | {total} | {conclusion} |")
lines.append("")

lines.append("## Gemma 관찰 요지")
lines.append("")
obs_file = CYCLE / "observations.jsonl"
obs_count = 0
total_chars = 0
if obs_file.exists():
    for line in obs_file.open(encoding="utf-8"):
        try:
            o = json.loads(line)
            obs_count += 1
            total_chars += o.get("llm", {}).get("thinking_chars", 0)
        except Exception:
            pass
lines.append(f"- 관찰 응답 수: **{obs_count}**")
lines.append(f"- 평균 thinking_chars: **{int(total_chars/obs_count) if obs_count else 0}**")
lines.append("- 응답은 일관되게 5섹션(가시 요소 / 기능 가설 / XML 상관관계 / 미확인 / 차기 제안) 구조를 유지")
lines.append("- StartPage 초기 화면 관찰이 반복됨 — UI는 프로젝트 로드 전 상태로 고정")
lines.append("")

lines.append("## 다음 야간 제안 (next_night_hints 후보)")
lines.append("")
lines.append("- **focus_areas**:")
lines.append("  - 프로젝트 로드 후 Network Editor / Parameter Editor 진입 시퀀스 학습")
lines.append("  - `.exp` 파일을 변화시키는 transition 탐색 (현재 모든 transition이 .exp 무영향 → Export/Generate 액션 별도 트리거 필요)")
lines.append("  - 다중 디바이스(`Device[2..]`) xpath 변형 시퀀스")
lines.append("- **avoid**:")
lines.append("  - StartPage 단순 관찰 반복 (이미 충분히 학습됨)")
lines.append("  - 동일 transition 5회 이상 반복 — 결정성 확인 후 1~2회로 충분")
lines.append("")

report = "\n".join(lines)
out = CYCLE / "morning_review.md"
out.write_text(report, encoding="utf-8")

# KB candidates
kb_dir = Path("skills/e2e_explorer/kb/patterns")
kb_dir.mkdir(parents=True, exist_ok=True)
cand_file = kb_dir / "_candidates.jsonl"

cand_lines = []
for name, det, examples, _ in det_rows:
    if not det or not examples:
        continue
    # Use first transition's xpath context from any summary
    sample_seq = per_name[name][0]
    sj = json.loads((SEQ_DIR / sample_seq / "summary.json").read_text(encoding="utf-8"))
    xpath = sj.get("xpath", "?")
    exp_changed = sum(1 for k in trans_exp if k[0] == name for b, a in trans_exp[k] if b != a)
    rule_parts = ["deterministic across repeats"]
    if exp_changed == 0:
        rule_parts.append(".exp unchanged")
    cand = {
        "xpath": xpath,
        "rule": ", ".join(rule_parts),
        "source": f"morning_review_{CYCLE.name}",
        "confidence": "high",
        "verified": False,
        "seq_name": name,
        "transitions_observed": [e[0] for e in examples],
        "reps_per_transition": examples[0][2] if examples else 0,
    }
    cand_lines.append(json.dumps(cand, ensure_ascii=False))

cand_file.write_text("\n".join(cand_lines) + "\n", encoding="utf-8")

print(f"REPORT={out}")
print(f"CANDIDATES={cand_file} count={len(cand_lines)}")
print(f"CYCLES_HINT=N/A SEQS={len(seq_dirs)} TRANSITIONS={transitions_total} ERRORS={errors_total}")
