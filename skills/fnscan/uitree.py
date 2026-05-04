"""uitree.py — MultiTool 실행 및 UIA 트리 덤프"""

import json
import time
from pathlib import Path

MT_EXE_PATTERN = r"C:\Program Files (x86)\Epec\MultiTool Creator {ver}\MultiToolCreator.exe"


def dump_ui_tree(ver: str, out_path: Path):
    """MultiTool 실행 → UIA 전체 트리 순회 → JSON 저장"""
    try:
        from pywinauto import Application
    except ImportError:
        print("  [WARN] pywinauto 미설치 — UIA 트리 덤프 skip")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("{}")
        return

    exe = MT_EXE_PATTERN.format(ver=ver)
    app = Application(backend="uia").start(exe)
    time.sleep(3)
    win = app.top_window()
    tree = _walk(win.wrapper_object())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(tree, ensure_ascii=False, indent=2))
    app.kill()


def _walk(elem, depth: int = 0) -> dict:
    try:
        rect = elem.rectangle()
        node = {
            "name":          elem.element_info.name,
            "automation_id": elem.element_info.automation_id,
            "control_type":  elem.element_info.control_type,
            "rect":          [rect.left, rect.top, rect.right, rect.bottom],
            "children":      []
        }
        if depth < 6:
            for child in elem.children():
                node["children"].append(_walk(child, depth + 1))
        return node
    except Exception:
        return {}
