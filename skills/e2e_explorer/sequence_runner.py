"""JSON 시퀀스 실행기 — XML 직접 편집 + 관찰 데이터 캡처.

시퀀스 형식 (sequences/*.json):
{
  "name": "can1_bitrate",
  "goal": "CAN1 BitRate 변경",
  "xpath": "/MtProject/Device[1]/CANs/CAN/BitRate",
  "values": ["500", "1000", "250"],
  "restore_on_finish": true
}

각 step:
  1. before snapshot
  2. xml set_text → after snapshot
  3. observation 기록
  4. (선택) restore
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

import xml_utils

log = logging.getLogger(__name__)


def run_sequence(seq: dict, project: Path, obs_dir: Path, snapshot_fn) -> dict:
    """단일 시퀀스 실행. snapshot_fn은 observer.snapshot_project."""
    name = seq["name"]
    xpath = seq["xpath"]
    values: list[str] = seq["values"]
    restore_on_finish = seq.get("restore_on_finish", True)

    seq_id = f"{time.strftime('%Y%m%d_%H%M%S')}_{name}_{uuid.uuid4().hex[:6]}"
    seq_dir = obs_dir / seq_id
    seq_dir.mkdir(parents=True, exist_ok=True)

    # 시작 전 백업 (복원용)
    bak = xml_utils.backup(project, suffix=f"seq_{name}")
    log.info("[%s] backup → %s", name, bak.name)

    initial = xml_utils.get_text(project, xpath)
    steps: list[dict] = []
    summary = {
        "seq_id": seq_id,
        "name": name,
        "xpath": xpath,
        "initial": initial,
        "steps": steps,
        "errors": [],
    }

    try:
        for i, new_val in enumerate(values):
            log.info("[%s] step %d: %s → %s", name, i, xpath, new_val)
            before_snap = snapshot_fn(project, seq_dir, label=f"step{i}_before")
            try:
                old, new = xml_utils.set_text(project, xpath, new_val)
            except Exception as e:
                summary["errors"].append({"step": i, "error": str(e)})
                log.exception("[%s] set_text failed", name)
                break
            after_snap = snapshot_fn(project, seq_dir, label=f"step{i}_after")
            steps.append({
                "i": i,
                "xpath": xpath,
                "old": old,
                "new": new,
                "before": before_snap,
                "after": after_snap,
                "ts": time.time(),
            })
    finally:
        if restore_on_finish:
            xml_utils.restore(project, bak)
            log.info("[%s] restored from backup", name)
        else:
            log.info("[%s] backup kept at %s (no restore)", name, bak.name)
        summary["backup_path"] = str(bak)

    # 시퀀스 요약 저장
    (seq_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return summary


def load_sequences(seq_dir: Path) -> list[dict]:
    seqs = []
    for f in sorted(seq_dir.glob("*.json")):
        try:
            seqs.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            log.warning("skip %s: %s", f.name, e)
    return seqs


def _cli() -> None:
    import argparse
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from observer import snapshot_project

    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--sequence", required=True, help="단일 JSON 시퀀스 파일")
    ap.add_argument("--out", required=True, help="observations 출력 디렉토리")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    seq = json.loads(Path(args.sequence).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    res = run_sequence(seq, Path(args.project), out, snapshot_project)
    print(json.dumps({"seq_id": res["seq_id"], "steps": len(res["steps"]), "errors": len(res["errors"])}, indent=2))


if __name__ == "__main__":
    _cli()
