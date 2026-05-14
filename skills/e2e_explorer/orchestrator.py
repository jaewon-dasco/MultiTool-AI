"""야간 관찰 루프 (v0.1).

- MultiTool 시작 대기
- N분 간격으로 UI 트리 dump + .mtproject 스냅샷
- Gemma4에 관찰 데이터 전송, 응답 누적
- 06:00 또는 --until-minutes 도달 시 종료 + summary.md 작성

읽기 전용 — GUI 입력·파일 변경 없음.
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import signal
import sys
import time
from pathlib import Path

# 같은 폴더 모듈 import (orchestrator 단독 실행 시)
sys.path.insert(0, str(Path(__file__).parent))

from kb_store import KB
from observer import snapshot_project
from ollama_client import OllamaClient
from sequence_runner import load_sequences, run_sequence
from ui_driver import dump_tree, is_running, start_multitool, wait_for_window

log = logging.getLogger("orchestrator")

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROJECT = ROOT / "MultiToolProject" / "E2EProject" / "DasDemoProject.mtproject"
KB_ROOT = ROOT / "skills" / "e2e_explorer" / "kb"
LOG_ROOT = ROOT / "logs" / "e2e"
PROMPT_PATH = Path(__file__).parent / "prompts" / "observe.md"

_stop = False


def _handle_sigterm(*_: object) -> None:
    global _stop
    _stop = True
    log.warning("SIGTERM received — finishing current step then exiting")


def _now_in_window(end_dt: dt.datetime) -> bool:
    return dt.datetime.now() < end_dt


def _excerpt_xml(path: Path, max_chars: int = 8000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:max_chars]
    except Exception as e:
        return f"<excerpt error: {e}>"


def run_cycle(
    project: Path,
    until: dt.datetime,
    interval_seconds: int,
    no_llm: bool,
) -> dict:
    kb = KB(KB_ROOT, LOG_ROOT)
    log.info("cycle date=%s until=%s interval=%ds", kb.cycle_date, until.isoformat(), interval_seconds)

    # 시스템 프롬프트 로드
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    # MultiTool 보장
    if not is_running():
        log.info("starting MultiTool...")
        start_multitool(str(project), wait_seconds=60)
    else:
        log.info("MultiTool already running, waiting for window...")
        wait_for_window(30)

    llm = None
    if not no_llm:
        llm = OllamaClient()
        if not llm.health():
            log.warning("Ollama health check failed — continuing without LLM")
            llm = None

    stats = {"steps": 0, "trees": 0, "snapshots": 0, "llm_calls": 0, "errors": 0}

    while _now_in_window(until) and not _stop:
        step_idx = stats["steps"]
        log.info("=== step %d ===", step_idx)
        try:
            # 1. UI 트리 dump
            tree = dump_tree(max_depth=10)
            tree_path = kb.save_ui_tree(tree, label=f"step{step_idx:03d}")
            stats["trees"] += 1
            log.info("ui_tree → %s", tree_path.name)

            # 2. .mtproject + .exp 스냅샷
            snap = snapshot_project(project, kb.snap_dir, label=f"step{step_idx:03d}")
            stats["snapshots"] += 1
            log.info("snapshot project + %d exp files", len(snap.get("exp_files", [])))

            # 3. Gemma 관찰 (옵션)
            llm_resp = None
            if llm is not None:
                obs_payload = {
                    "step": step_idx,
                    "ui_tree": tree,
                    "mtproject_excerpt": _excerpt_xml(project),
                }
                r = llm.observe(system_prompt, obs_payload)
                llm_resp = {
                    "content": r["content"],
                    "thinking_chars": len(r.get("thinking") or ""),
                }
                stats["llm_calls"] += 1
                log.info("llm content[:120]=%r", r["content"][:120])

            kb.append_observation({
                "step": step_idx,
                "tree_file": str(tree_path),
                "snapshot": snap,
                "llm": llm_resp,
            })
        except Exception as e:
            log.exception("step %d failed", step_idx)
            kb.append_failure({"step": step_idx, "error": str(e)})
            stats["errors"] += 1
        finally:
            stats["steps"] += 1

        # sleep with periodic stop check
        for _ in range(interval_seconds):
            if _stop or not _now_in_window(until):
                break
            time.sleep(1)

    kb.write_summary(stats)
    log.info("cycle done: %s", stats)
    return stats


def run_sequence_cycle(
    project: Path,
    until: dt.datetime,
    no_llm: bool,
    sequences_dir: Path,
) -> dict:
    """시퀀스 모드 — sequences/*.json을 반복 실행하며 관찰 데이터 누적."""
    kb = KB(KB_ROOT, LOG_ROOT)
    log.info("sequence cycle date=%s until=%s", kb.cycle_date, until.isoformat())

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    # MultiTool 보장 (UI 트리 캡처용)
    if not is_running():
        start_multitool(str(project), wait_seconds=60)
    else:
        wait_for_window(30)

    llm = None
    if not no_llm:
        llm = OllamaClient()
        if not llm.health():
            log.warning("Ollama health check failed — continuing without LLM")
            llm = None

    seqs = load_sequences(sequences_dir)
    log.info("loaded %d sequences from %s", len(seqs), sequences_dir)
    if not seqs:
        log.error("no sequences found — exiting")
        return {"seqs_run": 0, "errors": 1}

    stats = {"cycles": 0, "seqs_run": 0, "steps_total": 0, "llm_calls": 0, "errors": 0}
    obs_dir = kb.cycle_dir / "sequences"
    obs_dir.mkdir(parents=True, exist_ok=True)

    cycle_idx = 0
    while _now_in_window(until) and not _stop:
        log.info("=== cycle %d ===", cycle_idx)
        for seq in seqs:
            if _stop or not _now_in_window(until):
                break
            try:
                result = run_sequence(seq, project, obs_dir, snapshot_project)
                stats["seqs_run"] += 1
                stats["steps_total"] += len(result.get("steps", []))
                stats["errors"] += len(result.get("errors", []))

                if llm is not None:
                    obs_payload = {
                        "sequence": seq["name"],
                        "goal": seq.get("goal", ""),
                        "xpath": seq.get("xpath", ""),
                        "transitions": [
                            {"i": s["i"], "old": s["old"], "new": s["new"]}
                            for s in result["steps"]
                        ],
                        "mtproject_excerpt": _excerpt_xml(project, max_chars=4000),
                    }
                    r = llm.observe(system_prompt, obs_payload)
                    stats["llm_calls"] += 1
                    kb.append_observation({
                        "cycle": cycle_idx,
                        "seq_id": result["seq_id"],
                        "seq_name": seq["name"],
                        "n_steps": len(result["steps"]),
                        "llm_content": r["content"],
                        "llm_thinking_chars": len(r.get("thinking") or ""),
                    })
                    log.info("[%s] llm:%s", seq["name"], r["content"][:100])
                else:
                    kb.append_observation({
                        "cycle": cycle_idx,
                        "seq_id": result["seq_id"],
                        "seq_name": seq["name"],
                        "n_steps": len(result["steps"]),
                    })
            except Exception as e:
                log.exception("[%s] sequence failed", seq.get("name", "?"))
                kb.append_failure({"seq": seq.get("name"), "error": str(e)})
                stats["errors"] += 1
        cycle_idx += 1
        stats["cycles"] = cycle_idx
        log.info("cycle %d done · stats=%s", cycle_idx, stats)

    kb.write_summary(stats)
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=str(DEFAULT_PROJECT))
    ap.add_argument("--until", default="06:00", help="HH:MM (오늘 또는 내일)")
    ap.add_argument("--until-minutes", type=int, default=None, help="지금부터 N분")
    ap.add_argument("--interval", type=int, default=300, help="step 간 sleep 초 (기본 5분)")
    ap.add_argument("--observation-only", action="store_true", help="(deprecated, v0.1 호환)")
    ap.add_argument("--mode", choices=["observe", "sequence"], default="sequence",
                    help="observe: 동일 화면 반복 관찰 · sequence: XML 시퀀스 학습 (기본)")
    ap.add_argument("--sequences-dir", default=str(Path(__file__).parent / "sequences"))
    ap.add_argument("--no-llm", action="store_true", help="Gemma 호출 생략")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    signal.signal(signal.SIGTERM, _handle_sigterm)
    try:
        signal.signal(signal.SIGINT, _handle_sigterm)
    except Exception:
        pass

    # 종료 시각 산출
    now = dt.datetime.now()
    if args.until_minutes is not None:
        until = now + dt.timedelta(minutes=args.until_minutes)
    else:
        hh, mm = args.until.split(":")
        until = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
        if until <= now:
            until += dt.timedelta(days=1)

    log.info("E2E orchestrator mode=%s starting — until %s",
             args.mode, until.isoformat(timespec="seconds"))
    if args.mode == "sequence":
        stats = run_sequence_cycle(
            project=Path(args.project),
            until=until,
            no_llm=args.no_llm,
            sequences_dir=Path(args.sequences_dir),
        )
    else:
        stats = run_cycle(
            project=Path(args.project),
            until=until,
            interval_seconds=args.interval,
            no_llm=args.no_llm,
        )
    log.info("final stats: %s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
