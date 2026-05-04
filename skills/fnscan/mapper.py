"""mapper.py — UIA 메뉴 트리 → function_map.json 생성"""

import json
from pathlib import Path


def build_function_map(ui_tree: dict, out_path: Path):
    """uitree.dump_ui_tree() 결과에서 function_map.json 생성"""
    fmap: dict = {}

    # 메뉴바 항목
    for top in ui_tree.get("items", []):
        top_name = top["name"]
        for item in top.get("children", []):
            name = item.get("name", "").strip()
            if not name or name.startswith("MultiTool."):
                continue
            fmap[name] = {
                "shortcut":          item.get("shortcut", ""),
                "shortcut_verified": False,
                "menu_path":         [top_name, name],
                "automation_id":     item.get("automation_id", ""),
                "coordinates":       item.get("coordinates", []),
                "dialog":            "none",
                "source":            "menubar"
            }

    # 컨텍스트 메뉴 / 플로팅 툴바 / Network Editor 툴바 항목
    PATH_PREFIX_MAP = {
        "device":         "context:device",
        "device_toolbar": "toolbar",
        "ne_toolbar":     "ne_toolbar",
    }
    for ctx_type, ctx_items in ui_tree.get("context_menus", {}).items():
        if ctx_type == "_device_config":
            continue
        path_prefix = PATH_PREFIX_MAP.get(ctx_type, f"context:{ctx_type}")
        for item in ctx_items:
            name = item.get("name", "").strip()
            if not name or name.startswith("MultiTool."):
                continue
            if name not in fmap:
                fmap[name] = {
                    "shortcut":          item.get("shortcut", ""),
                    "shortcut_verified": False,
                    "menu_path":         [path_prefix, name],
                    "automation_id":     item.get("automation_id", ""),
                    "coordinates":       item.get("coordinates", []),
                    "dialog":            "none",
                    "source":            path_prefix
                }

    # 디바이스 Configuration 탭 — 탭 자체 + 각 탭의 입력 컨트롤
    cfg = ui_tree.get("context_menus", {}).get("_device_config", {})
    for tab_name, tab_data in cfg.items():
        if isinstance(tab_data, dict) and "error" in tab_data:
            continue
        tab_key = f"Configure: {tab_name}"
        if tab_key not in fmap:
            entry = {
                "shortcut":          "",
                "shortcut_verified": False,
                "menu_path":         ["Configure", tab_name],
                "automation_id":     "",
                "coordinates":       [],
                "dialog":            "DeviceConfigureView",
                "source":            "device_config",
                "inputs":            tab_data.get("inputs", []),
                "labels":            tab_data.get("labels", []),
            }
            tb = tab_data.get("toolbar_buttons")
            if tb:
                entry["toolbar_buttons"] = tb
            fmap[tab_key] = entry

        # OD 탭의 toolbar 버튼은 별도 function_map 항목으로 등록
        for tb in tab_data.get("toolbar_buttons", []):
            tip = tb.get("tooltip", "").strip()
            if not tip: continue
            key = f"{tab_name}: {tip}"
            if key not in fmap:
                fmap[key] = {
                    "shortcut":          "",
                    "shortcut_verified": False,
                    "menu_path":         ["Configure", tab_name, tip],
                    "automation_id":     "",
                    "coordinates":       [tb.get("x", 0), tb.get("y", 0)],
                    "dialog":            "none",
                    "source":            f"device_config_toolbar:{tab_name}",
                }

    out_path.write_text(json.dumps(fmap, ensure_ascii=False, indent=2), encoding="utf-8")
