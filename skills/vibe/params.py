"""params.py — 자연어 텍스트 → 구조화 파라미터 추출

extract(text) → {"devices": [...], "od_indices": [...], "bitrates": [...], "raw": text}

Claude tool call에서 비어있는 인자를 보완하거나, 사용자 명령에서 hex/bitrate 등을
정규화할 때 호출. LLM이 직접 채울 수도 있으므로 강제 검증은 하지 않는다.
"""

from __future__ import annotations

import re
from typing import TypedDict


# CU-3606-21, CU360621, MultiTool-3606 등 — Epec 디바이스 명명 규칙 기반
DEVICE_RE  = re.compile(r"\b([A-Z]{2,4})[\s-]?(\d{3,5})(?:[\s-]?(\d{1,3}))?\b")

# 0x2300, 2300h, 0x2A00:1
HEX_RE     = re.compile(r"\b(?:0x([0-9A-Fa-f]+)|([0-9A-Fa-f]{3,4})h)\b")

# 250kbps, 500K, 1M, 125 kbps
BITRATE_RE = re.compile(r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)\s*([kKmM])(?:bps|bit\/s|b\/s|B)")


class Device(TypedDict):
    family:  str  # 예: "CU"
    model:   str  # 예: "3606"
    variant: str  # 예: "21" (없으면 "")
    raw:     str


class Extracted(TypedDict):
    devices:    list[Device]
    od_indices: list[int]
    bitrates:   list[int]
    raw:        str


def extract_devices(text: str) -> list[Device]:
    out: list[Device] = []
    for m in DEVICE_RE.finditer(text):
        out.append({
            "family":  m.group(1),
            "model":   m.group(2),
            "variant": m.group(3) or "",
            "raw":     m.group(0),
        })
    return out


def extract_od_indices(text: str) -> list[int]:
    out: list[int] = []
    for m in HEX_RE.finditer(text):
        h = m.group(1) or m.group(2)
        try:
            out.append(int(h, 16))
        except ValueError:
            continue
    return out


def extract_bitrates(text: str) -> list[int]:
    """kbps 단위 정수로 정규화. 1M → 1000."""
    out: list[int] = []
    for m in BITRATE_RE.finditer(text):
        n     = float(m.group(1))
        unit  = m.group(2).lower()
        kbps  = int(n * (1000 if unit == "m" else 1))
        out.append(kbps)
    return out


def extract(text: str) -> Extracted:
    return {
        "devices":    extract_devices(text),
        "od_indices": extract_od_indices(text),
        "bitrates":   extract_bitrates(text),
        "raw":        text,
    }


if __name__ == "__main__":
    import sys, json
    sys.stdout.reconfigure(encoding="utf-8")
    samples = [
        "CU-3606-21 추가하고 CAN1 250kbps로 설정",
        "ScanDemo 열고 OD 0x2300 추가",
        "OD 2200h 삭제, bitrate 1Mbps",
        "비례밸브 RPDO 매핑 추가",
    ]
    for s in samples:
        print(s)
        print(" ", json.dumps(extract(s), ensure_ascii=False))
