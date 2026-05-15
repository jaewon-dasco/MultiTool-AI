#!/usr/bin/env python3
"""Deep verification of the test scenario against current .mtproject state."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")

tree = ET.parse(PROJ)
root = tree.getroot()

def localtag(e): return e.tag.split('}')[-1]
def child_text(parent, name):
    for c in parent:
        if localtag(c) == name: return c.text
    return None
def find_all(node, tag):
    out = []
    def walk(n):
        for c in n:
            if localtag(c) == tag: out.append(c)
            walk(c)
    walk(node)
    return out

# Top-level Device elements (children of root)
top_devs = [c for c in root if localtag(c) == "Device"]
print("="*70)
print(f"TOP-LEVEL DEVICES: {len(top_devs)}")
print("="*70)

devices = []
for d in top_devs:
    guid = d.get("Guid","?")
    info = {"guid": guid, "guid8": guid[:8]}
    # Walk children for key fields
    for c in d:
        tag = localtag(c)
        if tag in ("UnitName","Name","Model","TypeName","DeviceTypeName","UnitTypeName","CodesysVersion","Type","DeviceType","UnitType","Description"):
            if c.text and tag not in info:
                info[tag] = c.text
        if tag == "UnitType":
            info["UnitType"] = c.text or ""
    # CAN ports inside this device
    cans_in_dev = find_all(d, "CAN")
    # filter only fully-populated (have CANNumber child)
    full_cans = [c for c in cans_in_dev if any(localtag(x) == "CANNumber" for x in c)]
    info["cans"] = []
    for c in full_cans:
        info["cans"].append({
            "guid": c.get("Guid","?"),
            "number": child_text(c, "CANNumber"),
            "bitrate": child_text(c, "BitRate"),
            "communicates_with": child_text(c, "CommunicatesWithGuid"),
        })
    devices.append(info)

for d in devices:
    name = d.get("UnitName") or d.get("Name") or d.get("Description") or "?"
    typ = d.get("UnitType") or d.get("DeviceType") or d.get("TypeName") or d.get("Model") or "?"
    cds = d.get("CodesysVersion","?")
    print(f"\n[{d['guid8']}] {name}")
    print(f"  type={typ}  CDS={cds}  CAN ports={len(d['cans'])}")
    for c in d["cans"]:
        print(f"    CAN#{c['number']} BitRate={c['bitrate']} guid={c['guid'][:8]} commWith={c['communicates_with'][:8] if c['communicates_with'] else '-'}")

# Networks
print()
print("="*70)
print("NETWORKS")
print("="*70)
all_nets = find_all(root, "Network")
# Dedupe by id
seen=set(); unique_nets=[]
for n in all_nets:
    if id(n) not in seen: seen.add(id(n)); unique_nets.append(n)
# Filter: only those with Name
real_nets = []
for n in unique_nets:
    nm = child_text(n,"Name")
    if nm: real_nets.append((nm,n))

for nm, n in real_nets:
    br = child_text(n, "Bitrate") or child_text(n,"BitRate")
    nodes = find_all(n, "Node")
    print(f"\n{nm}  BitRate={br}  nodes={len(nodes)}")
    for nd in nodes:
        target = nd.get("Target") or child_text(nd,"Target")
        print(f"  Node target={target[:8] if target else '-'}")

# Build device guid lookup
guid_to_name = {d["guid"]: (d.get("UnitName") or d.get("Name") or "?") for d in devices}

# Determine which device each CAN guid belongs to + map CAN -> network connection
print()
print("="*70)
print("CAN ↔ NETWORK MAPPING (via CommunicatesWithGuid)")
print("="*70)
# Build set of CAN guids per network
network_can_pairs = defaultdict(list)
# For each CAN with CommunicatesWithGuid set, find which CAN it points to and group as pair
all_cans_global = []
for d in devices:
    for c in d["cans"]:
        all_cans_global.append({"dev": d.get("UnitName") or "?", "dev_guid": d["guid"], **c})
can_by_guid = {c["guid"]: c for c in all_cans_global}

# Group networks by mutual CommunicatesWithGuid pairs
groups = []
visited = set()
for c in all_cans_global:
    if c["guid"] in visited: continue
    if c["communicates_with"]:
        partner = can_by_guid.get(c["communicates_with"])
        if partner:
            visited.add(c["guid"]); visited.add(partner["guid"])
            groups.append([c, partner])
        else:
            visited.add(c["guid"]); groups.append([c])
    else:
        visited.add(c["guid"]); groups.append([c])

for i, g in enumerate(groups, 1):
    devs = " + ".join(f"{x['dev']}.CAN{x['number']}({x['bitrate']})" for x in g)
    print(f"  Group {i}: {devs}")

# .exp files
print()
print("="*70)
print(".exp FILES")
print("="*70)
exps = sorted(Path("MultiToolProject/E2EProject").rglob("*.exp"))
for e in exps:
    print(f"  {e.relative_to('MultiToolProject/E2EProject')}  {e.stat().st_size} bytes")

# === Spec verification ===
print()
print("="*70)
print("SPEC VERIFICATION")
print("="*70)
expected_devices = [
    ("5050-82", "controller", "2.3"),
    ("3720-21", "controller", "2.3"),
    ("3606-21", "controller", "2.3"),
    ("3724-01", "controller", "2.3"),
    ("6807-220", "monitor", "3.5"),
]
expected_nets = [
    ("NETWORK1", "250"),
    ("NETWORK2", "500"),
    ("NETWORK3", "1000"),
]

# Find device type by looking for model number anywhere in device subtree
all_xml = PROJ.read_text(encoding="utf-8", errors="replace")
print()
for model, role, cds in expected_devices:
    found = model in all_xml
    cds_for_model = "?"
    # crude: find occurrences of the model and look for CodesysVersion nearby
    print(f"  device {model:10} ({role}, CDS{cds}): {'present' if found else 'MISSING'}")

print()
for name, br in expected_nets:
    match = [n for nm,n in real_nets if nm == name]
    if not match:
        print(f"  {name}: MISSING")
        continue
    actual_br = child_text(match[0], "Bitrate") or child_text(match[0],"BitRate")
    ok = actual_br == br
    print(f"  {name} BitRate: {actual_br} (expect {br}) {'✓' if ok else '✗'}")

# 3724-01 single device check: find a device with model 3724 having a CAN with BitRate 250 and no CommWith
print()
print("3724-01 standalone:")
print("  (heuristic: device whose CAN has CommunicatesWithGuid empty/null + BitRate 250)")
for d in devices:
    nm = d.get("UnitName") or "?"
    for c in d["cans"]:
        if c["bitrate"] == "250" and not c["communicates_with"]:
            print(f"    {nm}.CAN{c['number']} matches (standalone, 250 kbit/s)")
