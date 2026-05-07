"""run.py — vibe CLI 진입점

사용법:
  py skills/vibe/run.py "명령"                            기본 (8.4, MultiTool 자동 시작)
  py skills/vibe/run.py "명령" --project DemoProject/ScanDemo/ScanDemo.mtproject
  py skills/vibe/run.py "명령" --version 8.4 --no-execute (dry-run, session.execute skip)
  py skills/vibe/run.py "명령" --before before.json --after after.json
                                                          (실행 전후 .mtproject snapshot diff)

환경변수:
  ANTHROPIC_API_KEY     필수
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agent   import run as run_agent             # noqa: E402
from session import Session, decide_method       # noqa: E402
from verify  import snapshot, diff               # noqa: E402

ROOT = Path(__file__).parent.parent.parent


class DryRunSession:
    """session.execute를 호출하지 않고 dispatch 결정만 기록."""
    def __init__(self):
        self.log: list[dict] = []
        self.project = None

    def execute(self, name: str, info: dict, params: dict) -> dict:
        method, detail = decide_method(info)
        entry = {"function": name, "method": method, "detail": detail,
                 "params": params, "dialog": info.get("dialog", "none"),
                 "dry_run": True}
        self.log.append(entry)
        return entry

    # 보조 tool — 실제 입력 없이 기록만
    def aux_type_text(self, text: str) -> dict:
        entry = {"action": "type_text", "text": text, "dry_run": True}
        self.log.append(entry)
        return entry

    def aux_press_key(self, key: str) -> dict:
        if key not in {"enter", "escape", "tab", "space", "backspace"}:
            raise ValueError(f"unsupported key: {key}")
        entry = {"action": "press_key", "key": key, "dry_run": True}
        self.log.append(entry)
        return entry

    def aux_wait(self, seconds: float) -> dict:
        entry = {"action": "wait", "seconds": float(seconds), "dry_run": True}
        self.log.append(entry)
        return entry

    # XML 패치 tools — dry-run에서도 동일 입력 검증
    _VALID_BITRATES = {10, 20, 50, 100, 125, 250, 500, 800, 1000}
    def xml_set_bitrate(self, can_number: int, bitrate: int) -> dict:
        if bitrate not in self._VALID_BITRATES:
            raise ValueError(f"invalid bitrate {bitrate}; allowed: {sorted(self._VALID_BITRATES)}")
        entry = {"action": "xml_set_bitrate", "can_number": can_number,
                 "bitrate": bitrate, "dry_run": True}
        self.log.append(entry); return entry

    def xml_set_buffering(self, can_number: int, enabled: bool) -> dict:
        entry = {"action": "xml_set_buffering", "can_number": can_number,
                 "enabled": enabled, "dry_run": True}
        self.log.append(entry); return entry

    def xml_set_j1939(self, can_number: int, enabled: bool) -> dict:
        entry = {"action": "xml_set_j1939", "can_number": can_number,
                 "enabled": enabled, "dry_run": True}
        self.log.append(entry); return entry

    def xml_show(self) -> dict:
        # 프로젝트가 설정돼 있으면 실 read_state 호출 (dry-run에서도 안전 — 읽기만)
        if self.project:
            import importlib.util
            mod_path = Path(__file__).parent.parent / "mtpatch" / "run.py"
            spec = importlib.util.spec_from_file_location("mtpatch_run", mod_path)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            state = mod.read_state(self.project)
            entry = {"action": "xml_show", "dry_run": True, **state}
        else:
            entry = {"action": "xml_show", "dry_run": True,
                     "project": None, "cans": [], "devices": []}
        self.log.append(entry); return entry


def main() -> int:
    p = argparse.ArgumentParser(description="vibecoding 자연어 → MultiTool 자동화")
    p.add_argument("command", help="자연어 명령")
    p.add_argument("--version",    default="8.4", help="MultiTool 버전")
    p.add_argument("--project",    default=None, help=".mtproject 경로 (선택)")
    p.add_argument("--no-execute", action="store_true", help="dry-run (UI 조작 skip)")
    p.add_argument("--before",     default=None, help="실행 전 snapshot 저장 경로")
    p.add_argument("--after",      default=None, help="실행 후 snapshot 저장 경로")
    p.add_argument("--max-iter",   type=int, default=12)
    p.add_argument("--model",      default="claude-opus-4-7")
    args = p.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    project_path = Path(args.project).resolve() if args.project else None
    snap_before  = None
    if project_path and args.before:
        snap_before = snapshot(project_path)
        Path(args.before).write_text(
            json.dumps(snap_before, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[snap] before → {args.before}")

    if args.no_execute:
        sess = DryRunSession()
    else:
        sess = Session(version=args.version)
        sess.start(project=project_path)

    try:
        result = run_agent(
            args.command, sess,
            version=args.version, model=args.model,
            max_iterations=args.max_iter,
        )
    finally:
        if not args.no_execute and hasattr(sess, "close"):
            sess.close()

    print("─" * 60)
    print(f"final: {result['final_text']}")
    print(f"iter:  {result['iterations']}  stop: {result['stop_reason']}")
    u = result["usage"]
    print(f"usage: in={u['input']} out={u['output']} "
          f"cache_read={u['cache_read']} cache_creation={u['cache_creation']}")
    print(f"session log ({len(result['session_log'])}):")
    for e in result["session_log"]:
        print(f"  - {e.get('function')} via {e.get('method')}({e.get('detail','')})")

    if project_path and args.after:
        snap_after = snapshot(project_path)
        Path(args.after).write_text(
            json.dumps(snap_after, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[snap] after  → {args.after}")
        if snap_before:
            d = diff(snap_before, snap_after)
            print(f"[diff] {json.dumps(d, ensure_ascii=False, indent=2)}")

    return 0 if result["stop_reason"] == "end_turn" else 1


if __name__ == "__main__":
    sys.exit(main())
