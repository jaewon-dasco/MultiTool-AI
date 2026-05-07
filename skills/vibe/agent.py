"""agent.py — Claude API tool 루프 + prompt cache

run(user_cmd, session, *, version, model)
  → user_cmd 자연어 → tool call 시퀀스 → session 실행 → 최종 응답 반환

prompt cache: tools 배열의 마지막 항목과 system 프롬프트에 cache_control={"type":"ephemeral"}.
tools는 함수 호출 분리 가능한 위치(렌더 순서: tools → system → messages)에서
가장 큰 정적 블록이므로 cache_read 효과가 가장 크다.

Opus 4.7 정책: thinking adaptive, sampling 파라미터(temperature/top_p/top_k) 미사용.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent.parent

from tools  import build_tools, exec_tool, NAME_TO_FUNC  # noqa: E402
from params import extract                                # noqa: E402

DEFAULT_MODEL = "claude-opus-4-7"
SYSTEM_PROMPT = (
    "EPEC MultiTool Creator GUI를 자동 조작하는 에이전트. "
    "사용자 자연어 명령을 function_map에 정의된 tool 호출 시퀀스로 분해해 실행한다. "
    "단축키(shortcut_verified=true)가 있는 항목은 우선 사용. "
    "device_config 다이얼로그가 필요한 항목은 inputs 파라미터를 채워서 호출. "
    "tool 호출 후 결과(method/detail)를 확인해 다음 단계를 결정. "
    "\n\n"
    "[보조 tool 사용 패턴]\n"
    "Open Project·Save As 등 OS 파일 다이얼로그를 여는 단축키를 호출한 직후에는 "
    "다음 시퀀스로 다이얼로그를 처리한다:\n"
    "  1. wait(seconds=1.5)         — 다이얼로그 로드 안정화\n"
    "  2. type_text(text=<절대 경로>) — 파일 경로 입력\n"
    "  3. press_key(key=\"enter\")     — 확정\n"
    "  4. wait(seconds=5)           — 프로젝트 로드 안정화\n"
    "잘못된 다이얼로그가 떴거나 취소가 필요하면 press_key(\"escape\"). "
    "Edit 컨트롤에 값을 입력해야 하는 device_config 다이얼로그도 type_text/press_key로 보강 가능.\n\n"
    "[GUI 우회 — XML 직접 편집]\n"
    "사용자가 .mtproject를 명시했고 단순 필드 변경(BitRate, Buffering, J1939)이면 "
    "Configure: CAN 다이얼로그 대신 xml_set_bitrate/xml_set_buffering/xml_set_j1939를 우선 사용. "
    "GUI 조작 없이 즉시 적용되며 자동 백업이 생성된다. "
    "현재 상태 확인은 xml_show.\n\n"
    "[알려진 한계]\n"
    "- 'Close Project' 단독 기능은 MultiTool에 없음. 다른 프로젝트를 Open Project로 여는 것이 "
    "사실상 닫기. 앱 자체 종료(Exit, Alt+F4)는 사용자 명시 확인 필요.\n"
    "- Bit Rate는 {10,20,50,100,125,250,500,800,1000} kbps만 유효. 그 외 값 요청 시 거절·재질문.\n"
    "- 도메인 위반(NodeId 0 또는 >127, 음수 등) 입력은 실행하지 말고 사용자에게 재확인.\n\n"
    "전 단계 완료 시 한 줄 요약."
)


def _attach_cache(tools: list[dict]) -> list[dict]:
    """마지막 tool에 cache_control 부착 → tools 전체 prefix 캐싱."""
    if not tools:
        return tools
    tools[-1] = {**tools[-1], "cache_control": {"type": "ephemeral"}}
    return tools


def _system_blocks() -> list[dict]:
    return [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ]


def run(
    user_cmd: str,
    session: Any,
    *,
    version: str = "8.4",
    model: str = DEFAULT_MODEL,
    max_iterations: int = 12,
    max_tokens: int = 16000,
) -> dict:
    """자연어 명령을 실행하고 결과 dict 반환.

    Returns:
      {"final_text": str, "iterations": int, "stop_reason": str,
       "session_log": list, "usage": {input,output,cache_read,cache_creation}}
    """
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("pip install anthropic") from e

    fmap_path = ROOT / "docs" / "versions" / version / "function_map.json"
    if not fmap_path.exists():
        raise FileNotFoundError(fmap_path)

    tools = _attach_cache(build_tools(fmap_path))
    client = anthropic.Anthropic()

    extracted = extract(user_cmd)
    hint_lines: list[str] = []
    if extracted["devices"]:
        hint_lines.append(f"devices: {extracted['devices']}")
    if extracted["od_indices"]:
        hint_lines.append(f"od_indices(int): {extracted['od_indices']}")
    if extracted["bitrates"]:
        hint_lines.append(f"bitrates(kbps): {extracted['bitrates']}")
    user_payload = user_cmd
    if hint_lines:
        user_payload = user_cmd + "\n\n[parsed hints]\n" + "\n".join(hint_lines)

    msgs: list[dict] = [{"role": "user", "content": user_payload}]
    final_text = ""
    stop_reason = ""
    usage_total = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0}

    for i in range(max_iterations):
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            system=_system_blocks(),
            tools=tools,
            messages=msgs,
        )
        u = resp.usage
        usage_total["input"]          += u.input_tokens
        usage_total["output"]         += u.output_tokens
        usage_total["cache_read"]     += getattr(u, "cache_read_input_tokens", 0) or 0
        usage_total["cache_creation"] += getattr(u, "cache_creation_input_tokens", 0) or 0

        msgs.append({"role": "assistant", "content": resp.content})
        stop_reason = resp.stop_reason or ""

        if stop_reason != "tool_use":
            for b in resp.content:
                if getattr(b, "type", None) == "text":
                    final_text += b.text
            return {
                "final_text":   final_text.strip(),
                "iterations":   i + 1,
                "stop_reason":  stop_reason,
                "session_log":  list(getattr(session, "log", [])),
                "usage":        usage_total,
            }

        results = [
            exec_tool(b, session)
            for b in resp.content
            if getattr(b, "type", None) == "tool_use"
        ]
        msgs.append({"role": "user", "content": results})

    return {
        "final_text":  final_text.strip() or "[max_iterations 도달]",
        "iterations":  max_iterations,
        "stop_reason": "max_iterations",
        "session_log": list(getattr(session, "log", [])),
        "usage":       usage_total,
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[INFO] ANTHROPIC_API_KEY 미설정 — build_tools 검증만 수행")
    tools = _attach_cache(build_tools())
    last = tools[-1]
    print(f"tools: {len(tools)}, last_has_cache_control: {'cache_control' in last}")
    print(f"system_blocks: {_system_blocks()}")
