"""mtpatch/run.py — .mtproject XML 직접 편집 (UI 자동화 대안)

GUI 우회 — `.mtproject` XML을 직접 mutate하고 backup·diff로 안전성 보장.
지원 연산:
  set-bitrate <project> <can#> <bitrate>           CAN/BitRate 변경
  set-buffering <project> <can#> <true|false>      CAN/Settings/Buffering
  set-j1939 <project> <can#> <true|false>          J1939 활성/비활성
  set-node-id <project> <can#> <id>                NodeId
  set-heartbeat <project> <can#> <ms>              HeartbeatInterval
  show <project>                                   현재 핵심 필드 출력
  backup <project>                                 .mtproject.bak.<ts> 생성
  restore <project> <bak>                          backup으로 복구

write 호출 시 자동으로 sibling 백업(.bak.<timestamp>) 생성.
편집 후 verify.snapshot diff 검증을 사용자가 실행하도록 권장.
"""

from __future__ import annotations

import argparse
import datetime
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


def _parse(path: Path) -> tuple[ET.ElementTree, ET.Element]:
    tree = ET.parse(path)
    return tree, tree.getroot()


def _backup(path: Path) -> Path:
    ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = path.with_suffix(path.suffix + f".bak.{ts}")
    shutil.copy2(path, dst)
    return dst


def _write(tree: ET.ElementTree, path: Path) -> None:
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _find_can(root: ET.Element, can_number: int) -> Optional[ET.Element]:
    """root-level Device/CANs/CAN[CANNumber=<n>] 검색."""
    for can in root.findall("./Device/CANs/CAN"):
        num = can.findtext("CANNumber")
        if num and int(num) == can_number:
            return can
    return None


def _set_text(parent: ET.Element, child_tag: str, value: str) -> bool:
    el = parent.find(child_tag)
    if el is None:
        return False
    el.text = value
    return True


# ───────────────────────── 명령 핸들러 ─────────────────────────

def read_state(project: Path) -> dict:
    """프로젝트 핵심 필드를 dict로 반환 (LLM·CLI 공용)."""
    _, root = _parse(project)
    cans_data = []
    for can in root.findall("./Device/CANs/CAN"):
        s = can.find("Settings")
        cans_data.append({
            "number":    int(can.findtext("CANNumber",  "0") or 0),
            "bitrate":   int(can.findtext("BitRate",    "0") or 0),
            "buffering": (s.findtext("Buffering",        "") if s is not None else "") == "true",
            "node_id":   int(s.findtext("NodeId",          "0") or 0) if s is not None else 0,
            "heartbeat_ms": int(s.findtext("HeartbeatInterval", "0") or 0) if s is not None else 0,
            "j1939":     (can.findtext("J1939/J1939EnableRequestMessage", "") == "true"),
        })
    devices = [{"guid": d.attrib.get("Guid", ""),
                "name": d.findtext("Name", ""),
                "id":   d.findtext("Id",   "")}
               for d in root.findall("./Device")]
    return {"project": str(project), "cans": cans_data, "devices": devices}


def cmd_show(project: Path) -> dict:
    state = read_state(project)
    print(f"project: {state['project']}")
    print(f"  CANs: {len(state['cans'])}")
    for c in state["cans"]:
        print(f"  CAN{c['number']}: bitrate={c['bitrate']} buffering={c['buffering']} "
              f"node_id={c['node_id']} heartbeat={c['heartbeat_ms']}ms j1939={c['j1939']}")
    print(f"  Devices: {len(state['devices'])}")
    for d in state["devices"]:
        print(f"    - {d['guid']}  name={d['name']!r}  id={d['id']!r}")
    return state


VALID_BITRATES = {10, 20, 50, 100, 125, 250, 500, 800, 1000}


def cmd_set_bitrate(project: Path, can_number: int, bitrate: int) -> int:
    if bitrate not in VALID_BITRATES:
        raise ValueError(f"invalid bitrate {bitrate}; allowed: {sorted(VALID_BITRATES)}")
    tree, root = _parse(project)
    can = _find_can(root, can_number)
    if can is None:
        raise ValueError(f"CAN{can_number} not found in {project.name}")
    if not _set_text(can, "BitRate", str(bitrate)):
        raise ValueError("BitRate element missing")
    bak = _backup(project)
    _write(tree, project)
    print(f"  CAN{can_number}.BitRate = {bitrate}")
    print(f"  backup: {bak.name}")
    return 0


def cmd_set_buffering(project: Path, can_number: int, enabled: bool) -> int:
    tree, root = _parse(project)
    can = _find_can(root, can_number)
    if can is None:
        print(f"[ERROR] CAN{can_number} 없음"); return 1
    settings = can.find("Settings")
    if settings is None:
        print(f"[ERROR] Settings 없음"); return 1
    if not _set_text(settings, "Buffering", "true" if enabled else "false"):
        print(f"[ERROR] Buffering 엘리먼트 없음"); return 1
    bak = _backup(project)
    _write(tree, project)
    print(f"  CAN{can_number}.Buffering = {enabled} | backup: {bak.name}")
    return 0


def cmd_set_j1939(project: Path, can_number: int, enabled: bool) -> int:
    tree, root = _parse(project)
    can = _find_can(root, can_number)
    if can is None:
        print(f"[ERROR] CAN{can_number} 없음"); return 1
    if not _set_text(can, "J1939/J1939EnableRequestMessage",
                     "true" if enabled else "false"):
        print(f"[ERROR] J1939 엘리먼트 없음"); return 1
    bak = _backup(project)
    _write(tree, project)
    print(f"  CAN{can_number}.J1939 = {enabled} | backup: {bak.name}")
    return 0


def cmd_set_node_id(project: Path, can_number: int, node_id: int) -> int:
    tree, root = _parse(project)
    can = _find_can(root, can_number)
    if can is None:
        print(f"[ERROR] CAN{can_number} 없음"); return 1
    settings = can.find("Settings")
    if settings is None or not _set_text(settings, "NodeId", str(node_id)):
        print(f"[ERROR] NodeId 엘리먼트 없음"); return 1
    bak = _backup(project)
    _write(tree, project)
    print(f"  CAN{can_number}.NodeId = {node_id} | backup: {bak.name}")
    return 0


def cmd_set_heartbeat(project: Path, can_number: int, ms: int) -> int:
    tree, root = _parse(project)
    can = _find_can(root, can_number)
    if can is None:
        print(f"[ERROR] CAN{can_number} 없음"); return 1
    settings = can.find("Settings")
    if settings is None or not _set_text(settings, "HeartbeatInterval", str(ms)):
        print(f"[ERROR] HeartbeatInterval 엘리먼트 없음"); return 1
    bak = _backup(project)
    _write(tree, project)
    print(f"  CAN{can_number}.HeartbeatInterval = {ms}ms | backup: {bak.name}")
    return 0


def cmd_backup(project: Path) -> int:
    bak = _backup(project)
    print(f"  → {bak}")
    return 0


def cmd_restore(project: Path, bak: Path) -> int:
    if not bak.exists():
        print(f"[ERROR] backup 없음: {bak}"); return 1
    shutil.copy2(bak, project)
    print(f"  restored: {bak.name} → {project.name}")
    return 0


# ───────────────────────── CLI ─────────────────────────

def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="mtpatch", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def _add_can(parser):
        parser.add_argument("project", type=Path)
        parser.add_argument("can_number", type=int)

    sp = sub.add_parser("show");          sp.add_argument("project", type=Path)
    sp = sub.add_parser("set-bitrate");   _add_can(sp); sp.add_argument("bitrate", type=int)
    sp = sub.add_parser("set-buffering"); _add_can(sp); sp.add_argument("enabled", choices=["true","false"])
    sp = sub.add_parser("set-j1939");     _add_can(sp); sp.add_argument("enabled", choices=["true","false"])
    sp = sub.add_parser("set-node-id");   _add_can(sp); sp.add_argument("node_id", type=int)
    sp = sub.add_parser("set-heartbeat"); _add_can(sp); sp.add_argument("ms", type=int)
    sp = sub.add_parser("backup");        sp.add_argument("project", type=Path)
    sp = sub.add_parser("restore");       sp.add_argument("project", type=Path); sp.add_argument("bak", type=Path)
    args = p.parse_args()

    try:
        if args.cmd == "show":           cmd_show(args.project);                                                 return 0
        if args.cmd == "set-bitrate":    return cmd_set_bitrate(args.project, args.can_number, args.bitrate)
        if args.cmd == "set-buffering":  return cmd_set_buffering(args.project, args.can_number, args.enabled == "true")
        if args.cmd == "set-j1939":      return cmd_set_j1939(args.project, args.can_number, args.enabled == "true")
        if args.cmd == "set-node-id":    return cmd_set_node_id(args.project, args.can_number, args.node_id)
        if args.cmd == "set-heartbeat":  return cmd_set_heartbeat(args.project, args.can_number, args.ms)
        if args.cmd == "backup":         return cmd_backup(args.project)
        if args.cmd == "restore":        return cmd_restore(args.project, args.bak)
    except (ValueError, FileNotFoundError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
