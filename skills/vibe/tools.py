"""tools.py — function_map.json → Claude tool schema + 실행 wrapper

build_tools(fmap_path)        function_map → Anthropic tool schema 리스트
NAME_TO_FUNC[tool_name]       정규화 이름 → 원본 function_map 키
exec_tool(tool_use, session)  tool_use 블록 → MultiTool 조작 실행 → 결과 dict

도구 이름 정규화: "Save As..." → "save_as", "Configure: CAN" → "configure_can".
입력 스키마: device_config 항목은 `inputs` 배열에서 파라미터 추출, 그 외 항목은 빈 schema.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT     = Path(__file__).parent.parent.parent
FMAP     = ROOT / "docs" / "versions" / "8.4" / "function_map.json"
NAME_RE  = re.compile(r"[^a-zA-Z0-9_-]+")
NAME_TO_FUNC: dict[str, str]   = {}      # 정규화 이름 → 원본 이름
FMAP_CACHE:   dict[str, dict]  = {}      # 원본 이름 → info dict (모듈 로드 시 1회)

# function_map과 별개로 LLM에 노출되는 보조 UI tool. 파일 다이얼로그·확인창 등
# 다단계 시퀀스를 조합 가능하게 한다. session.aux_<name>(**input)로 dispatch.
AUX_TOOLS: list[dict] = [
    {
        "name": "type_text",
        "description": (
            "활성 창/다이얼로그에 텍스트를 타이핑한다. "
            "Open Project(Ctrl+Shift+O) 같은 단축키 직후 파일 경로를 입력하거나 "
            "Edit 컨트롤에 값을 채울 때 사용. 호출 전 wait(seconds=1~2)로 다이얼로그 안정화 권장."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "타이핑할 텍스트 (절대 경로 권장)"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "press_key",
        "description": (
            "특수 키 1회 입력. type_text 후 enter로 다이얼로그 확정, "
            "잘못된 다이얼로그 escape로 닫기 등에 사용."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "enum": ["enter", "escape", "tab", "space", "backspace"],
                    "description": "키 이름",
                },
            },
            "required": ["key"],
        },
    },
    {
        "name": "wait",
        "description": (
            "지정 초만큼 대기. 단축키 직후(다이얼로그 로드)·Enter 후(프로젝트 로드) 등 "
            "UI 안정화 대기용. 0.5~8초 권장."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "seconds": {"type": "number", "description": "대기 시간(초)"},
            },
            "required": ["seconds"],
        },
    },
]
AUX_NAMES = {t["name"] for t in AUX_TOOLS}


# .mtproject XML 직접 편집 tool — GUI 우회. session.xml_<name>(**input)로 dispatch.
# session.project가 설정돼 있을 때만 동작 (대상 .mtproject 명시 필요).
XML_TOOLS: list[dict] = [
    {
        "name": "xml_set_bitrate",
        "description": (
            "현재 프로젝트의 CAN<n> Bit Rate를 직접 XML에서 변경 (GUI 우회). "
            "MultiTool UI 조작 없이 즉시 적용 — Configure: CAN 다이얼로그 폴백."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "can_number": {"type": "integer", "description": "CAN 번호 (1부터)"},
                "bitrate":    {"type": "integer", "description": "kbps (예: 125, 250, 500, 1000)"},
            },
            "required": ["can_number", "bitrate"],
        },
    },
    {
        "name": "xml_set_buffering",
        "description": "CAN<n>.Settings.Buffering 토글 (GUI 우회).",
        "input_schema": {
            "type": "object",
            "properties": {
                "can_number": {"type": "integer"},
                "enabled":    {"type": "boolean"},
            },
            "required": ["can_number", "enabled"],
        },
    },
    {
        "name": "xml_set_j1939",
        "description": "CAN<n>.J1939EnableRequestMessage 토글 (GUI 우회).",
        "input_schema": {
            "type": "object",
            "properties": {
                "can_number": {"type": "integer"},
                "enabled":    {"type": "boolean"},
            },
            "required": ["can_number", "enabled"],
        },
    },
    {
        "name": "xml_show",
        "description": "현재 프로젝트의 핵심 필드(CAN bitrate, buffering, j1939, devices) 조회.",
        "input_schema": {"type": "object", "properties": {}},
    },
]
XML_NAMES = {t["name"] for t in XML_TOOLS}


def normalize_name(name: str) -> str:
    """'Configure: CAN' → 'configure_can', 'Save As...' → 'save_as'"""
    s = NAME_RE.sub("_", name).strip("_").lower()
    return s[:64]


def _params_for(info: dict) -> dict[str, Any]:
    """device_config 항목 inputs → JSON Schema properties.

    이름 없는 입력은 type+rect 기준 ordinal 식별자(ComboBox_1 등)로 대체."""
    props: dict[str, Any] = {}
    counters: dict[str, int] = {}
    for inp in info.get("inputs", []):
        nm = inp.get("name") or ""
        ty = inp.get("type", "Edit")
        if not nm:
            counters[ty] = counters.get(ty, 0) + 1
            nm = f"{ty}_{counters[ty]}"
        key = normalize_name(nm)
        if not key or key in props:
            continue
        if ty == "CheckBox":
            props[key] = {"type": "boolean", "description": f"{nm} (CheckBox)"}
        elif ty == "ComboBox":
            props[key] = {"type": "string", "description": f"{nm} (ComboBox, default={inp.get('value', '')})"}
        elif ty == "Slider":
            props[key] = {"type": "number", "description": f"{nm} (Slider)"}
        else:
            props[key] = {"type": "string", "description": f"{nm} ({ty}, default={inp.get('value', '')})"}
    return props


def to_tool(name: str, info: dict) -> dict:
    sc       = info.get("shortcut") or "none"
    verified = info.get("shortcut_verified", False)
    src      = info.get("source", "")
    desc     = f"{name} | shortcut={sc}{' (verified)' if verified else ''} | source={src}"
    if info.get("dialog") and info["dialog"] != "none":
        desc += f" | dialog={info['dialog']}"
    return {
        "name": normalize_name(name),
        "description": desc,
        "input_schema": {
            "type": "object",
            "properties": _params_for(info),
        },
    }


def build_tools(fmap_path: Path | str = FMAP) -> list[dict]:
    """function_map.json → tool schema 리스트 + AUX_TOOLS. NAME_TO_FUNC/FMAP_CACHE 갱신.

    AUX_TOOLS는 prefix(렌더 순서)에 안정적으로 들어가도록 마지막에 append한다.
    캐시 breakpoint도 변경 없이 마지막 항목에 부착되어 cache_read 효과 유지."""
    NAME_TO_FUNC.clear()
    FMAP_CACHE.clear()
    fmap = json.loads(Path(fmap_path).read_text(encoding="utf-8"))
    tools = []
    for orig, info in fmap.items():
        norm = normalize_name(orig)
        NAME_TO_FUNC[norm] = orig
        FMAP_CACHE[orig]   = info
        tools.append(to_tool(orig, info))
    tools.extend(AUX_TOOLS)
    tools.extend(XML_TOOLS)
    return tools


def exec_tool(tool_use: Any, session: Any) -> dict:
    """tool_use 블록 → function_map 항목 lookup → session 실행.

    Args:
        tool_use: Anthropic SDK ContentBlock (type=tool_use). dict 또는 attribute 접근 모두 허용.
        session:  Session 인스턴스 (skills.vibe.session.Session)

    Returns: {"tool_use_id": str, "type": "tool_result", "content": str, "is_error": bool}
    """
    name      = _attr(tool_use, "name")
    tu_id     = _attr(tool_use, "id")
    tu_input  = _attr(tool_use, "input") or {}

    # 1) 보조 tool — session.aux_<name>(**input)로 dispatch
    if name in AUX_NAMES:
        method = getattr(session, f"aux_{name}", None)
        if method is None:
            return _result(tu_id, f"session has no aux_{name}", error=True)
        try:
            result = method(**tu_input)
            return _result(tu_id, json.dumps(result, ensure_ascii=False), error=False)
        except Exception as e:
            return _result(tu_id, f"{type(e).__name__}: {e}", error=True)

    # 1b) XML 패치 tool — session.xml_<short>(**input)
    if name in XML_NAMES:
        short  = name[len("xml_"):]
        method = getattr(session, f"xml_{short}", None)
        if method is None:
            return _result(tu_id, f"session has no xml_{short}", error=True)
        try:
            result = method(**tu_input)
            return _result(tu_id, json.dumps(result, ensure_ascii=False), error=False)
        except Exception as e:
            return _result(tu_id, f"{type(e).__name__}: {e}", error=True)

    # 2) function_map tool
    orig = NAME_TO_FUNC.get(name)
    if not orig:
        return _result(tu_id, f"unknown tool: {name}", error=True)

    info = FMAP_CACHE.get(orig)
    if not info:
        return _result(tu_id, f"function_map miss: {orig} (build_tools 미실행?)", error=True)

    try:
        result = session.execute(orig, info, tu_input)
        return _result(tu_id, json.dumps(result, ensure_ascii=False), error=False)
    except Exception as e:
        return _result(tu_id, f"{type(e).__name__}: {e}", error=True)


def _attr(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _result(tu_id: str, content: str, error: bool) -> dict:
    return {
        "type": "tool_result",
        "tool_use_id": tu_id,
        "content": content,
        "is_error": error,
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    tools = build_tools()
    print(f"tools: {len(tools)}")
    for t in tools[:5]:
        print(f"  - {t['name']}: {t['description']}")
    print(f"  ...")
    print(f"NAME_TO_FUNC sample: {dict(list(NAME_TO_FUNC.items())[:3])}")
