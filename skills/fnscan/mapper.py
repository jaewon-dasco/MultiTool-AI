"""mapper.py — UIA 트리 → function_map.json 생성"""

import json
from pathlib import Path


def build_function_map(ui_tree: dict, out_path: Path):
    """UIA 트리 dict에서 MenuItem 항목을 추출해 function_map.json 저장"""
    fmap: dict = {}
    _extract_menu_items(ui_tree, [], fmap)
    out_path.write_text(json.dumps(fmap, ensure_ascii=False, indent=2))


def _extract_menu_items(node: dict, path: list, fmap: dict):
    if node.get("control_type") == "MenuItem" and node.get("name"):
        name     = node["name"].split("\t")[0].strip()
        shortcut = _parse_shortcut(node.get("name", ""))
        rect     = node.get("rect", [0, 0, 0, 0])
        cx       = (rect[0] + rect[2]) // 2
        cy       = (rect[1] + rect[3]) // 2
        fmap[name] = {
            "shortcut":          shortcut,
            "shortcut_verified": False,
            "menu_path":         path + [name],
            "automation_id":     node.get("automation_id", ""),
            "coordinates":       [cx, cy],
            "dialog":            "none"
        }
    for child in node.get("children", []):
        new_path = path + [node["name"]] if node.get("name") else path
        _extract_menu_items(child, new_path, fmap)


def _parse_shortcut(text: str) -> str:
    parts = text.split("\t")
    return parts[1].strip() if len(parts) > 1 else ""
