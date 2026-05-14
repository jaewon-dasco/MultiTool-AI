"""MultiTool GUI 컨트롤 트리 dump (읽기 전용).

v0.1: enumerate + dump만. 클릭/입력 코드 없음.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import psutil

log = logging.getLogger(__name__)

MULTITOOL_EXE = r"C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe"
MULTITOOL_PROC = "MultiTool.exe"
WINDOW_TITLE_HINT = "MultiTool"


def is_running() -> bool:
    for p in psutil.process_iter(attrs=["name"]):
        if (p.info["name"] or "").lower() == MULTITOOL_PROC.lower():
            return True
    return False


def start_multitool(project: str | None = None, wait_seconds: int = 30) -> bool:
    """MultiTool 시작. 이미 떠 있으면 skip. 메인 창 출현 대기."""
    from pywinauto import Application

    if is_running():
        log.info("MultiTool already running")
        return wait_for_window(wait_seconds)

    args = [MULTITOOL_EXE]
    if project:
        args.append(project)
    log.info("starting %s", args)
    Application(backend="uia").start(" ".join(f'"{a}"' for a in args))
    return wait_for_window(wait_seconds)


def wait_for_window(wait_seconds: int = 30) -> bool:
    from pywinauto import Desktop

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        try:
            wins = Desktop(backend="uia").windows()
            for w in wins:
                t = (w.window_text() or "")
                if WINDOW_TITLE_HINT.lower() in t.lower():
                    log.info("MultiTool window found: %r", t)
                    return True
        except Exception as e:
            log.debug("window scan: %s", e)
        time.sleep(1)
    log.warning("MultiTool window not found within %ds", wait_seconds)
    return False


def _ctrl_to_dict(c, depth: int, max_depth: int) -> dict[str, Any]:
    info: dict[str, Any] = {}
    try:
        info["name"] = c.window_text()
    except Exception:
        info["name"] = None
    try:
        info["type"] = c.element_info.control_type
    except Exception:
        info["type"] = None
    try:
        info["auto_id"] = c.element_info.automation_id
    except Exception:
        info["auto_id"] = None
    try:
        info["class"] = c.element_info.class_name
    except Exception:
        info["class"] = None
    try:
        info["enabled"] = c.is_enabled()
    except Exception:
        info["enabled"] = None
    try:
        info["visible"] = c.is_visible()
    except Exception:
        info["visible"] = None

    children = []
    if depth < max_depth:
        try:
            for ch in c.children():
                children.append(_ctrl_to_dict(ch, depth + 1, max_depth))
        except Exception as e:
            log.debug("children() failed at depth %d: %s", depth, e)
    info["children"] = children
    return info


def dump_tree(max_depth: int = 8) -> dict[str, Any]:
    """현재 활성 MultiTool 메인 창의 컨트롤 트리 dump."""
    from pywinauto import Desktop

    wins = Desktop(backend="uia").windows()
    target = None
    for w in wins:
        try:
            t = w.window_text() or ""
            if WINDOW_TITLE_HINT.lower() in t.lower():
                target = w
                break
        except Exception:
            continue
    if target is None:
        return {"error": "MultiTool window not found", "windows": [w.window_text() for w in wins]}

    return {
        "title": target.window_text(),
        "tree": _ctrl_to_dict(target, depth=0, max_depth=max_depth),
        "captured_at": time.time(),
    }


def _cli() -> None:
    import argparse, json

    ap = argparse.ArgumentParser()
    ap.add_argument("--start", action="store_true", help="MultiTool 시작")
    ap.add_argument("--project", default=None)
    ap.add_argument("--dump", action="store_true", help="트리 dump")
    ap.add_argument("--out", default="tree.json")
    ap.add_argument("--max-depth", type=int, default=8)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO)
    if args.start:
        ok = start_multitool(args.project)
        print(f"start: {ok}")
    if args.dump:
        tree = dump_tree(max_depth=args.max_depth)
        Path(args.out).write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"dumped → {args.out}")


if __name__ == "__main__":
    _cli()
