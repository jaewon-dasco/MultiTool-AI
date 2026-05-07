"""debug_scenarios.py — L2 시뮬레이션 (Claude API 호출 없이 LLM 의사결정 검증)

다양한 자연어 명령에 대해 사람-Claude가 직접 산출한 tool 시퀀스를 DryRunSession에
주입해 라우팅·로직을 검증한다. agent.run을 모킹하지 않고 직접 시퀀스를 정의해
"이 명령에 대해 LLM이 이렇게 분해할 것이다"를 명시적으로 표현 → 갭 발견.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

import tools
from run import DryRunSession


class FakeBlock:
    type = "tool_use"
    def __init__(self, _id, name, inp=None):
        self.id, self.name, self.input = _id, name, inp or {}


SCENARIOS: list[dict] = [
    {
        "command": "ScanDemo 프로젝트 열어줘",
        "sequence": [
            ("open_project", {}),
            ("wait",         {"seconds": 1.5}),
            ("type_text",    {"text": r"D:\4_AIProject\4_CoDeSys\AI_MutiTool\DemoProject\ScanDemo\ScanDemo.mtproject"}),
            ("press_key",    {"key": "enter"}),
            ("wait",         {"seconds": 5}),
        ],
    },
    {
        "command": "현재 프로젝트 저장",
        "sequence": [
            ("save_project", {}),
        ],
    },
    {
        "command": "CAN1 bitrate를 500으로 바꿔 (XML 우회)",
        "project": r"D:\4_AIProject\4_CoDeSys\AI_MutiTool\DemoProject\ScanDemo\ScanDemo.mtproject",
        "sequence": [
            ("xml_show",         {}),
            ("xml_set_bitrate",  {"can_number": 1, "bitrate": 500}),
        ],
    },
    {
        "command": "CAN1 bitrate 500, J1939 활성화 (XML 일괄)",
        "project": r"D:\4_AIProject\4_CoDeSys\AI_MutiTool\DemoProject\ScanDemo\ScanDemo.mtproject",
        "sequence": [
            ("xml_set_bitrate", {"can_number": 1, "bitrate": 500}),
            ("xml_set_j1939",   {"can_number": 1, "enabled": True}),
            ("xml_show",        {}),
        ],
    },
    {
        "command": "지금 프로젝트 System Export",
        "sequence": [
            ("system_export", {}),
        ],
    },
    {
        "command": "CAN1을 GUI로 250kbps에서 500kbps로 변경 (Configure: CAN 다이얼로그)",
        "sequence": [
            ("configure_can", {"bit_rate": "500"}),
        ],
    },
    {
        "command": "프로젝트 닫기",
        "sequence": [
            ("close_project", {}),
        ],
        "expected_error": "function_map 미수록 — system 프롬프트가 LLM에 대안 안내",
    },
    {
        "command": "Save As로 ScanDemo_v2 라는 이름으로 저장",
        "sequence": [
            ("save_as",   {}),
            ("wait",      {"seconds": 1.5}),
            ("type_text", {"text": r"D:\4_AIProject\4_CoDeSys\AI_MutiTool\DemoProject\ScanDemo_v2\ScanDemo_v2.mtproject"}),
            ("press_key", {"key": "enter"}),
            ("wait",      {"seconds": 5}),
        ],
    },
    {
        "command": "현재 프로젝트 정보 보여줘",
        "project": r"D:\4_AIProject\4_CoDeSys\AI_MutiTool\DemoProject\ScanDemo\ScanDemo.mtproject",
        "sequence": [
            ("xml_show", {}),  # GUI 조작 없이 즉시 반환
        ],
    },
    {
        "command": "ScanDemo 열고 CAN1을 500kbps로 (열기 + 변경 복합)",
        "sequence": [
            ("open_project", {}),
            ("wait",         {"seconds": 1.5}),
            ("type_text",    {"text": r"D:\...\ScanDemo.mtproject"}),
            ("press_key",    {"key": "enter"}),
            ("wait",         {"seconds": 5}),
            ("xml_set_bitrate", {"can_number": 1, "bitrate": 500}),  # 열린 후 즉시 XML 패치
        ],
    },
    {
        "command": "Bit Rate 0으로 설정 (도메인 위반 입력)",
        "project": r"D:\4_AIProject\4_CoDeSys\AI_MutiTool\DemoProject\ScanDemo\ScanDemo.mtproject",
        "sequence": [
            ("xml_set_bitrate", {"can_number": 1, "bitrate": 0}),
        ],
        "expected_error": "유효 bitrate 화이트리스트 외 — ValueError 정상",
    },
]


def run_scenario(idx: int, scn: dict) -> dict:
    print(f"\n[{idx}] 명령: {scn['command']}")
    sess = DryRunSession()
    if scn.get("project"):
        sess.project = Path(scn["project"])
    errors: list[str] = []
    for i, (name, inp) in enumerate(scn["sequence"], 1):
        block = FakeBlock(f"s{idx}.{i}", name, inp)
        res = tools.exec_tool(block, sess)
        ok  = "✓" if not res["is_error"] else "✗"
        print(f"   {i}. [{ok}] {name}({json.dumps(inp, ensure_ascii=False)})")
        if res["is_error"]:
            err = json.loads(res["content"]) if res["content"].startswith("{") else res["content"]
            print(f"        → ERROR: {err}")
            errors.append(f"{name}: {err}")
    return {"command":  scn["command"],
            "errors":   errors,
            "expected": scn.get("expected_error"),
            "log_len":  len(sess.log)}


def main():
    tools.build_tools()
    print("=" * 70)
    print("L2 시뮬레이션 — 자연어 명령 디버깅 (DryRunSession)")
    print("=" * 70)
    summary = []
    for i, scn in enumerate(SCENARIOS, 1):
        summary.append(run_scenario(i, scn))

    print("\n" + "=" * 70)
    print("결과 요약")
    print("=" * 70)
    real_fails = 0
    for s in summary:
        if not s["errors"]:
            tag = "OK         "
        elif s["expected"]:
            tag = "EXPECTED✗  "
        else:
            tag = "FAIL       "
            real_fails += 1
        print(f"  [{tag}] {s['command']}")
        for e in s["errors"]:
            note = f" ({s['expected']})" if s["expected"] else ""
            print(f"             → {e}{note}")
    print(f"\n실 FAIL: {real_fails}  /  EXPECTED 거절: {sum(1 for s in summary if s['errors'] and s['expected'])}  /  OK: {sum(1 for s in summary if not s['errors'])}")


if __name__ == "__main__":
    main()
