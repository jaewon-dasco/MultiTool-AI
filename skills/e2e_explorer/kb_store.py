"""Knowledge Base 저장소 — v0.1은 JSONL 추가 전용 + 디렉토리 관리."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class KB:
    def __init__(self, kb_root: Path, log_root: Path, cycle_date: str | None = None) -> None:
        self.kb_root = kb_root
        self.log_root = log_root
        self.cycle_date = cycle_date or time.strftime("%Y-%m-%d")
        self.cycle_dir = log_root / self.cycle_date
        self.obs_dir = self.cycle_dir / "observations"
        self.snap_dir = self.cycle_dir / "snapshots"
        self.tree_dir = self.cycle_dir / "ui_trees"
        self._init_dirs()

    def _init_dirs(self) -> None:
        for d in (self.kb_root, self.cycle_dir, self.obs_dir, self.snap_dir, self.tree_dir):
            d.mkdir(parents=True, exist_ok=True)

    def append_observation(self, record: dict[str, Any]) -> None:
        record = {"ts": time.time(), **record}
        path = self.cycle_dir / "observations.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def append_failure(self, record: dict[str, Any]) -> None:
        record = {"ts": time.time(), **record}
        path = self.kb_root / "failures.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def save_ui_tree(self, tree: dict, label: str = "") -> Path:
        ts = time.strftime("%Y%m%d_%H%M%S")
        suffix = f"_{label}" if label else ""
        path = self.tree_dir / f"{ts}{suffix}.json"
        path.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def write_summary(self, stats: dict[str, Any]) -> Path:
        lines = [
            f"# E2E 야간 사이클 보고 — {self.cycle_date}",
            "",
            "| 항목 | 값 |",
            "| ---- | -- |",
        ]
        for k, v in stats.items():
            lines.append(f"| {k} | {v} |")
        path = self.cycle_dir / "summary.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path
