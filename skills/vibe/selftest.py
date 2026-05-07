"""selftest.py — Claude API 호출 없이 vibe 파이프라인 직렬 검증

목적: anthropic 패키지·API 키 없이도 다음을 단일 실행으로 검증한다.
  1. params.py    — 자연어 추출
  2. tools.py     — function_map → tool schema 변환 + 이름 정규화
  3. tools.py     — exec_tool 라우팅 (모킹된 tool_use 블록)
  4. session.py   — decide_method + DryRunSession.execute
  5. verify.py    — snapshot + diff
  6. agent loop   — 모킹된 messages.create 응답으로 루프 동작

실행:
  py skills/vibe/selftest.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import params                                     # noqa: E402
import tools                                      # noqa: E402
from session import decide_method                 # noqa: E402
from verify  import snapshot, diff                # noqa: E402
from run     import DryRunSession                 # noqa: E402

ROOT = Path(__file__).parent.parent.parent
PASS, FAIL = "[PASS]", "[FAIL]"
results: list[tuple[str, str, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    tag = PASS if cond else FAIL
    results.append((tag, name, detail))
    print(f"{tag} {name}" + (f"  — {detail}" if detail else ""))


# ───────────────────────── 1. params ─────────────────────────
def t_params() -> None:
    cmd = "CU-3606-21 추가하고 CAN1 250kbps로 설정, OD 0x2300 추가"
    e   = params.extract(cmd)
    check("params.devices",    len(e["devices"])    == 1 and e["devices"][0]["model"]  == "3606")
    check("params.bitrates",   e["bitrates"]        == [250])
    check("params.od_indices", e["od_indices"]      == [0x2300])

    e2 = params.extract("OD 2200h, bitrate 1Mbps")
    check("params.hex_h_form",  e2["od_indices"]    == [0x2200])
    check("params.bitrate_M",   e2["bitrates"]      == [1000])


# ───────────────────────── 2. tools ─────────────────────────
def t_tools_schema() -> None:
    schemas = tools.build_tools()
    expected = 49 + len(tools.AUX_TOOLS) + len(tools.XML_TOOLS)
    check("tools.count==49+aux+xml",   len(schemas) == expected,
          f"expected {expected} got {len(schemas)}")
    check("tools.NAME_TO_FUNC populated", len(tools.NAME_TO_FUNC) == 49)
    check("tools.FMAP_CACHE populated",   len(tools.FMAP_CACHE)   == 49)
    check("tools.last_has_cache_field",   "name" in schemas[-1])
    all_names = {s["name"] for s in schemas}
    check("tools.aux_present",  tools.AUX_NAMES.issubset(all_names))
    check("tools.xml_present",  tools.XML_NAMES.issubset(all_names))

    # 정규화 이름 안정성
    check("normalize.save_as", tools.normalize_name("Save As...")     == "save_as")
    check("normalize.config",  tools.normalize_name("Configure: CAN") == "configure_can")

    # device_config 의 input schema 추출
    can = next(s for s in schemas if s["name"] == "configure_can")
    props = can["input_schema"]["properties"]
    check("tools.configure_can.has_props", len(props) > 0,
          f"{len(props)} properties: {list(props)[:3]}")


# ───────────────────────── 3. exec_tool 라우팅 ─────────────────────────
@dataclass
class FakeToolUse:
    """anthropic SDK ContentBlock(type=tool_use) 흉내."""
    id:    str
    name:  str
    input: dict
    type:  str = "tool_use"


def t_exec_tool() -> None:
    tools.build_tools()              # NAME_TO_FUNC + FMAP_CACHE 충전
    sess = DryRunSession()

    # case 1: 알려진 tool — open_project
    block = FakeToolUse(id="t1", name="open_project", input={})
    res = tools.exec_tool(block, sess)
    check("exec.open_project.ok",  res["is_error"] is False)
    check("exec.open_project.routed",
          sess.log[-1]["function"] == "Open Project" and
          sess.log[-1]["method"]   == "shortcut",
          str(sess.log[-1]))

    # case 2: 미지의 tool
    block = FakeToolUse(id="t2", name="bogus_tool_xyz", input={})
    res2 = tools.exec_tool(block, sess)
    check("exec.unknown.is_error", res2["is_error"] is True,
          res2["content"][:60])

    # case 3: device_config
    block = FakeToolUse(id="t3", name="configure_can", input={"bit_rate": "500"})
    res3 = tools.exec_tool(block, sess)
    check("exec.configure_can.ok", res3["is_error"] is False)
    check("exec.configure_can.dialog",
          sess.log[-1]["dialog"] == "DeviceConfigureView")

    # case 4: aux tools (type_text / press_key / wait)
    res4 = tools.exec_tool(FakeToolUse(id="t4", name="wait",
                                       input={"seconds": 0.0}), sess)
    check("exec.aux.wait.ok",        res4["is_error"] is False and
                                     sess.log[-1]["action"] == "wait")
    res5 = tools.exec_tool(FakeToolUse(id="t5", name="type_text",
                                       input={"text": "C:\\path\\file.mtproject"}), sess)
    check("exec.aux.type_text.ok",   res5["is_error"] is False and
                                     sess.log[-1]["text"].endswith(".mtproject"))
    res6 = tools.exec_tool(FakeToolUse(id="t6", name="press_key",
                                       input={"key": "enter"}), sess)
    check("exec.aux.press_key.ok",   res6["is_error"] is False and
                                     sess.log[-1]["key"] == "enter")
    res7 = tools.exec_tool(FakeToolUse(id="t7", name="press_key",
                                       input={"key": "bogus"}), sess)
    check("exec.aux.press_key.invalid", res7["is_error"] is True,
          res7["content"][:60])

    # case 5: XML tools
    res8 = tools.exec_tool(FakeToolUse(id="t8", name="xml_set_bitrate",
                                       input={"can_number": 1, "bitrate": 500}), sess)
    check("exec.xml.set_bitrate",   res8["is_error"] is False and
                                    sess.log[-1]["action"] == "xml_set_bitrate" and
                                    sess.log[-1]["bitrate"] == 500)
    res9 = tools.exec_tool(FakeToolUse(id="t9", name="xml_set_j1939",
                                       input={"can_number": 1, "enabled": True}), sess)
    check("exec.xml.set_j1939",     res9["is_error"] is False and
                                    sess.log[-1]["enabled"] is True)
    # xml_show — 프로젝트 미설정 시 빈 스키마
    res10 = tools.exec_tool(FakeToolUse(id="ta", name="xml_show", input={}), sess)
    check("exec.xml.show.schema",   res10["is_error"] is False and
                                    set(sess.log[-1].keys()) >= {"action","cans","devices"})

    # xml_show — 프로젝트 설정 시 실 read_state로 채워짐
    sess2 = DryRunSession()
    sess2.project = ROOT / "DemoProject" / "ScanDemo" / "ScanDemo.mtproject"
    if sess2.project.exists():
        tools.exec_tool(FakeToolUse(id="tb", name="xml_show", input={}), sess2)
        e = sess2.log[-1]
        check("exec.xml.show.real_state",
              len(e["cans"]) >= 1 and e["cans"][0]["bitrate"] > 0,
              str(e["cans"][:1]))


# ───────────────────────── 4. decide_method ─────────────────────────
def t_decide_method() -> None:
    # verified shortcut → shortcut
    m, d = decide_method({"shortcut": "Ctrl + Shift + N", "shortcut_verified": True})
    check("decide.verified_shortcut", m == "shortcut" and d == "Ctrl + Shift + N")

    # unverified shortcut + menu_path → menu (menu has higher priority over unverified shortcut)
    m, d = decide_method({"shortcut": "Ctrl + S", "shortcut_verified": False,
                          "menu_path": ["FILE", "Save Project"]})
    check("decide.menu_when_unverified", m == "menu" and "Save Project" in d)

    # only coords
    m, d = decide_method({"coordinates": [123, 456]})
    check("decide.coords", m == "coords" and d == "123,456")

    # nothing
    m, d = decide_method({})
    check("decide.none", m == "none")

    # dangerous shortcut → fallback
    m, d = decide_method({"shortcut": "Alt + F4", "shortcut_verified": True,
                          "menu_path": ["FILE", "Exit"]})
    check("decide.dangerous_skipped", m == "menu",
          f"got {m}/{d}")


# ───────────────────────── 5. verify ─────────────────────────
def t_mtpatch_cli_errors() -> None:
    """mtpatch CLI는 ValueError를 트레이스백 없이 [ERROR] + exit 1로 처리해야 한다."""
    import subprocess
    p = ROOT / "DemoProject" / "ScanDemo" / "ScanDemo.mtproject"
    if not p.exists():
        check("mtpatch.cli.skipped", True, "no sample"); return
    cmd = ["py", "-3", str(ROOT / "skills" / "mtpatch" / "run.py"),
           "set-bitrate", str(p), "1", "0"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    check("mtpatch.cli.exit_1",       r.returncode == 1, f"rc={r.returncode}")
    check("mtpatch.cli.no_traceback", "Traceback" not in (r.stderr + r.stdout),
          (r.stderr + r.stdout)[:200])
    check("mtpatch.cli.error_prefix", "[ERROR]" in (r.stderr + r.stdout))


def t_verify() -> None:
    p = ROOT / "DemoProject" / "ScanDemo" / "ScanDemo.mtproject"
    if not p.exists():
        check("verify.skipped", True, f"no sample at {p}")
        return
    snap = snapshot(p)
    check("verify.snapshot.devices",  len(snap["devices"]) == 1)
    check("verify.snapshot.template", snap["devices"][0]["template"].startswith("3606"))

    # 자기-자신 diff → 변경 없음
    d = diff(snap, snap)
    empty = all(len(v) == 0 for cat in d.values() for v in cat.values())
    check("verify.diff.identity_zero", empty)


# ───────────────────────── 6. agent loop (모킹) ─────────────────────────
class FakeMessages:
    """resp 시퀀스를 차례로 반환하는 가짜 client.messages."""
    def __init__(self, responses: list[Any]):
        self.responses = list(responses)
        self.calls     = 0

    def create(self, **kw):
        self.calls += 1
        if not self.responses:
            raise AssertionError("FakeMessages: 응답 시퀀스 소진")
        return self.responses.pop(0)


def _resp(content: list, stop_reason: str):
    usage = SimpleNamespace(
        input_tokens=100, output_tokens=20,
        cache_read_input_tokens=0, cache_creation_input_tokens=0,
    )
    return SimpleNamespace(content=content, stop_reason=stop_reason, usage=usage)


def t_agent_loop_mock() -> None:
    # agent.py가 anthropic 모듈을 import하므로, 가짜 모듈을 sys.modules에 주입
    fake_anthropic = SimpleNamespace(Anthropic=lambda: SimpleNamespace(
        messages=FakeMessages([
            # 첫 응답: tool_use (open_project)
            _resp(
                [FakeToolUse(id="u1", name="open_project", input={})],
                stop_reason="tool_use",
            ),
            # 두 번째 응답: 텍스트 종료
            _resp(
                [SimpleNamespace(type="text", text="프로젝트 열기 완료.")],
                stop_reason="end_turn",
            ),
        ]),
    ))
    sys.modules["anthropic"] = fake_anthropic

    # 새 import 강제 (이전 import된 캐시 무효)
    if "agent" in sys.modules:
        del sys.modules["agent"]
    import agent  # noqa: E402

    sess = DryRunSession()
    result = agent.run("ScanDemo 열어줘", sess, version="8.4")
    check("agent.iterations==2", result["iterations"]  == 2)
    check("agent.stop==end_turn", result["stop_reason"] == "end_turn")
    check("agent.final_text",     "프로젝트" in result["final_text"],
          result["final_text"])
    check("agent.session_log_len", len(result["session_log"]) == 1)
    check("agent.routed_open_project",
          result["session_log"][0]["function"] == "Open Project")


def t_agent_dialog_compose_mock() -> None:
    """LLM이 단축키 + 보조 tool을 조합해 다이얼로그 처리하는 시나리오."""
    fake_anthropic = SimpleNamespace(Anthropic=lambda: SimpleNamespace(
        messages=FakeMessages([
            # turn 1: open_project + wait (parallel tool_use 가능)
            _resp(
                [FakeToolUse(id="u1", name="open_project", input={}),
                 FakeToolUse(id="u2", name="wait", input={"seconds": 1.5})],
                stop_reason="tool_use",
            ),
            # turn 2: type_text
            _resp(
                [FakeToolUse(id="u3", name="type_text",
                             input={"text": r"D:\proj\ScanDemo.mtproject"})],
                stop_reason="tool_use",
            ),
            # turn 3: press_key enter + wait
            _resp(
                [FakeToolUse(id="u4", name="press_key", input={"key": "enter"}),
                 FakeToolUse(id="u5", name="wait",      input={"seconds": 5})],
                stop_reason="tool_use",
            ),
            # turn 4: 종료
            _resp(
                [SimpleNamespace(type="text", text="프로젝트 로드 완료.")],
                stop_reason="end_turn",
            ),
        ]),
    ))
    sys.modules["anthropic"] = fake_anthropic
    if "agent" in sys.modules:
        del sys.modules["agent"]
    import agent  # noqa: E402

    sess = DryRunSession()
    r = agent.run("ScanDemo 프로젝트 열어줘", sess, version="8.4")
    check("dialog.iterations==4",  r["iterations"]  == 4)
    check("dialog.stop==end_turn", r["stop_reason"] == "end_turn")
    actions = [e.get("action") or e.get("function") for e in r["session_log"]]
    check("dialog.full_sequence",
          actions == ["Open Project", "wait", "type_text", "press_key", "wait"],
          str(actions))


# ───────────────────────── 실행 ─────────────────────────
def main() -> int:
    print("=== vibe selftest (no API) ===\n")
    for fn in (t_params, t_tools_schema, t_exec_tool,
               t_decide_method, t_verify, t_mtpatch_cli_errors,
               t_agent_loop_mock, t_agent_dialog_compose_mock):
        print(f"\n--- {fn.__name__} ---")
        try:
            fn()
        except Exception as e:
            check(fn.__name__, False, f"EXCEPTION: {type(e).__name__}: {e}")

    print("\n=== summary ===")
    p = sum(1 for r in results if r[0] == PASS)
    f = sum(1 for r in results if r[0] == FAIL)
    print(f"PASS={p}  FAIL={f}")
    if f:
        print("\nfailed:")
        for tag, name, det in results:
            if tag == FAIL:
                print(f"  - {name}: {det}")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
