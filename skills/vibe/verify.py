"""verify.py — .mtproject XML 구조 diff + 의도 일치 검증

snapshot(path)         경로 → 정규화된 dict (디바이스/네트워크/OD 등 핵심 키)
diff(before, after)    추가·삭제·변경 요약
intent_match(diff, intent)  의도 키워드 vs diff 매칭 — pass/fail 사유 반환

대용량 XML 전체 비교 대신 의미있는 노드만 추출해 비교한다(.mtproject는 SDK 빌드/메타
필드가 매번 갱신되어 raw diff는 노이즈가 큼).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def snapshot(path: str | Path) -> dict[str, Any]:
    """meaningful 노드만 추출. .mtproject는 Device가 여러 위치에서 등장하므로
    GUID 기준으로 합쳐 단일 레코드로 만든다."""
    p    = Path(path)
    root = ET.parse(p).getroot()

    by_guid: dict[str, dict] = {}
    for d in root.findall(".//MachineType/Devices/Device"):
        g = d.attrib.get("Guid", "")
        by_guid.setdefault(g, {"guid": g})["template"] = d.findtext("DeviceTemplate", "")
    for d in root.findall("./Device"):
        g = d.attrib.get("Guid", "")
        rec = by_guid.setdefault(g, {"guid": g})
        rec["name"] = d.findtext("Name", "")
        rec["id"]   = d.findtext("Id", "")

    networks = []
    for n in root.iter("Network"):
        networks.append({
            "guid":    n.attrib.get("Guid", ""),
            "name":    n.findtext("Name", ""),
            "type":    n.findtext("Type", ""),
            "bitrate": n.findtext("Bitrate", "") or n.findtext("BitRate", ""),
        })

    od_indices = []
    for idx in root.iter("ODIndex"):
        v = idx.attrib.get("Index") or idx.findtext("Index", "")
        if v:
            od_indices.append(v)

    return {
        "path":       str(p),
        "devices":    list(by_guid.values()),
        "networks":   networks,
        "od_indices": sorted(set(od_indices)),
    }


def _index_by(items: list[dict], key: str) -> dict[str, dict]:
    return {it.get(key, ""): it for it in items if it.get(key)}


def diff(before: dict, after: dict) -> dict[str, Any]:
    out: dict[str, Any] = {"added": {}, "removed": {}, "changed": {}}
    for cat in ("devices", "networks"):
        b = _index_by(before.get(cat, []), "guid")
        a = _index_by(after.get(cat, []), "guid")
        out["added"][cat]   = [a[g] for g in a.keys() - b.keys()]
        out["removed"][cat] = [b[g] for g in b.keys() - a.keys()]
        out["changed"][cat] = [
            {"before": b[g], "after": a[g]}
            for g in b.keys() & a.keys() if b[g] != a[g]
        ]
    bo = set(before.get("od_indices", []))
    ao = set(after.get("od_indices", []))
    out["added"]["od_indices"]   = sorted(ao - bo)
    out["removed"]["od_indices"] = sorted(bo - ao)
    return out


def intent_match(d: dict, intent: dict) -> dict:
    """intent 예: {"add_device": "3606_21", "add_od": ["0x2300"], "set_bitrate": 250}.

    Returns: {"ok": bool, "reasons": [...]}
    """
    reasons: list[str] = []

    if (tmpl := intent.get("add_device")):
        added = d["added"].get("devices", [])
        if not any(tmpl in (a.get("template") or "") for a in added):
            reasons.append(f"add_device miss: {tmpl} not in {added}")

    if (ods := intent.get("add_od")):
        if isinstance(ods, str):
            ods = [ods]
        added_od = set(d["added"].get("od_indices", []))
        for o in ods:
            norm = o.lower().replace("0x", "")
            if not any(norm in (x or "").lower() for x in added_od):
                reasons.append(f"add_od miss: {o}")

    if (br := intent.get("set_bitrate")) is not None:
        chg = d["changed"].get("networks", [])
        if not any(str(br) in str(c["after"].get("bitrate", "")) for c in chg):
            reasons.append(f"set_bitrate miss: {br}")

    return {"ok": not reasons, "reasons": reasons}


if __name__ == "__main__":
    import sys, json
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) >= 3 and sys.argv[1] == "snapshot":
        print(json.dumps(snapshot(sys.argv[2]), ensure_ascii=False, indent=2))
    elif len(sys.argv) >= 4 and sys.argv[1] == "diff":
        b = snapshot(sys.argv[2]); a = snapshot(sys.argv[3])
        print(json.dumps(diff(b, a), ensure_ascii=False, indent=2))
    else:
        print(__doc__)
