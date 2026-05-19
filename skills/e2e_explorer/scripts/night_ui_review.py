#!/usr/bin/env python3
"""night_ui/{results,failures}.jsonl 분석 — 시드별 signal/noise + intent 추출.

dry-run으로 누적된 results를 ML signal 관점에서 검증:
  - 시드별 OK/FAIL 분포
  - 노이즈 (모든 run 공통 value_changes)
  - 의도 신호 (시드별 교집합 - 노이즈)
  - Baseline 정합화 전후 비교 (old: 28건 노이즈 / new: 0건)

사용:
  py night_ui_review.py [run_dir1] [run_dir2] ...
  기본: logs/e2e/night_ui_archive_* + logs/e2e/night_ui
"""
import sys, json
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "logs" / f"morning_review_{__import__('datetime').date.today()}.md"


def load_runs(dirs):
    all_rows = []
    for d in dirs:
        rp = d / "results.jsonl"
        if not rp.exists(): continue
        rows = [json.loads(l) for l in rp.open(encoding="utf-8")]
        for r in rows: r["__source"] = d.name
        all_rows.extend(rows)
    return all_rows


def analyze(rows, label=""):
    n = len(rows); ok = [r for r in rows if r.get("ok")]
    print(f"\n=== {label} ===")
    print(f"total={n} OK={len(ok)} FAIL={n-len(ok)} ({len(ok)/max(n,1)*100:.0f}%)")

    if not ok: return {}

    # Noise = changes appearing in ≥80% of OK runs (universal across seeds)
    all_changes = Counter()
    per_seed = defaultdict(list)
    for r in ok:
        seen = {(c["tag"], c["old"], c["new"]) for c in r.get("mt_diff", {}).get("value_changes", [])}
        for k in seen: all_changes[k] += 1
        per_seed[r["seed"]].append(seen)

    noise_threshold = len(ok) * 0.5
    noise = {k for k, c in all_changes.items() if c >= noise_threshold}
    print(f"노이즈 (≥50% 공통): {len(noise)}건")
    if noise:
        print("  예시:", list(noise)[:3])

    # value_changes distribution
    counts = sorted(len(s) for s in per_seed.values() for _ in (1,)) if False else \
             sorted(len(r.get("mt_diff", {}).get("value_changes", [])) for r in ok)
    if counts:
        print(f"value_changes 분포: min={counts[0]} median={counts[len(counts)//2]} max={counts[-1]} avg={sum(counts)/len(counts):.1f}")

    # Per-seed intent (intersection - noise)
    intents = {}
    for seed, sets in per_seed.items():
        if len(sets) < 2: continue
        common = set.intersection(*sets) - noise
        if common: intents[seed] = sorted(common)
    print(f"Intent 추출 시드: {len(intents)}건 / 총 {len(per_seed)}건")
    return {"n": n, "ok": len(ok), "fail": n-len(ok),
            "noise": noise, "per_seed_intent": intents,
            "vc_avg": sum(counts)/len(counts) if counts else 0}


def main():
    if len(sys.argv) > 1:
        dirs = [Path(a) for a in sys.argv[1:]]
    else:
        e2e = ROOT / "logs" / "e2e"
        dirs = sorted(e2e.glob("night_ui_archive_*")) + [e2e / "night_ui"]
    dirs = [d for d in dirs if d.exists()]
    print(f"분석 대상: {[d.name for d in dirs]}")

    archives = [d for d in dirs if "archive" in d.name]
    current = [d for d in dirs if d.name == "night_ui"]

    arch_stats = analyze(load_runs(archives), label="이전 baseline (archive 01:24)") if archives else None
    # "current" night_ui 폴더가 새 baseline 적용 후 재실행됐는지 results.jsonl 첫 행으로 추정
    is_post_fix = False
    if current and (current[0] / "results.jsonl").exists():
        first = next(iter((current[0] / "results.jsonl").open(encoding="utf-8")), None)
        if first:
            try:
                fr = json.loads(first)
                # post-fix baseline sha 시작 = bf669... 또는 635d... (clean_baseline 계열)
                bs = fr.get("before_mt_sha", "")
                is_post_fix = bs.startswith("bf669") or bs.startswith("635d") or bs.startswith("3f5f")
            except Exception: pass
    curr_label = "current (post-baseline-fix)" if is_post_fix else "current (pre-fix, 미재실행)"
    curr_stats = analyze(load_runs(current), label=curr_label) if current else None

    # 보고서 작성
    lines = [f"# Morning Review — {__import__('datetime').date.today()}", ""]
    lines.append("## 핵심 지표 비교\n")
    lines.append("| 지표 | 이전 baseline | 새 baseline | 변화 |")
    lines.append("| ---- | ------------- | ----------- | ---- |")
    if arch_stats and curr_stats:
        for k, lbl in [("n","총 시도"),("ok","성공"),("fail","실패"),("vc_avg","평균 value_changes")]:
            a = arch_stats.get(k, "-"); c = curr_stats.get(k, "-")
            if isinstance(a,(int,float)) and isinstance(c,(int,float)):
                delta = c-a; sign = "+" if delta>=0 else ""
                lines.append(f"| {lbl} | {a:.1f} | {c:.1f} | {sign}{delta:.1f} |")
            else:
                lines.append(f"| {lbl} | {a} | {c} | — |")

    if arch_stats:
        lines.append("\n## 이전 baseline 시드별 의도 변경 (Intent)\n")
        lines.append("set intersection - noise(≥50% 공통)으로 추출:")
        lines.append("\n| 시드 | 추출된 의도 변경 |")
        lines.append("| ---- | ---------------- |")
        for seed, intent in sorted(arch_stats.get("per_seed_intent", {}).items()):
            ev = ", ".join(f"`{t}: {o}→{n}`" for t,o,n in intent[:3])
            lines.append(f"| {seed} | {ev} |")

    lines.append("\n## 결론")
    if arch_stats and curr_stats:
        nz_a = len(arch_stats.get("noise", set()))
        nz_c = len(curr_stats.get("noise", set()))
        lines.append(f"- 노이즈 (모든 시드 공통 변경): {nz_a}건 → {nz_c}건")
        lines.append(f"- 평균 value_changes: {arch_stats.get('vc_avg',0):.1f} → {curr_stats.get('vc_avg',0):.1f}")
        if nz_c < nz_a:
            lines.append("- ✓ Baseline 정합화 효과 확인 (노이즈 감소)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n보고서: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
