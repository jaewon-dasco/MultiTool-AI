#!/usr/bin/env python3
"""Probe MultiTool UI tree, find BitRate-related controls."""
import sys, json
from pywinauto import Desktop, Application

# Connect to MultiTool
app = Application(backend="uia").connect(title_re=".*MultiTool Creator.*", timeout=10)
win = app.top_window()
print(f"Connected: {win.window_text()}")
print(f"Class: {win.class_name()}")

# Walk tree, collect interesting controls
def walk(ctrl, depth=0, out=None):
    if out is None: out = []
    try:
        info = {
            "depth": depth,
            "class": ctrl.class_name(),
            "name": ctrl.window_text()[:80],
            "auto_id": ctrl.automation_id() if hasattr(ctrl, "automation_id") else "",
            "ctrl_type": ctrl.element_info.control_type if hasattr(ctrl.element_info, "control_type") else "",
        }
        out.append(info)
    except Exception as e:
        out.append({"depth": depth, "err": str(e)})
        return out
    if depth > 20:
        return out
    try:
        for ch in ctrl.children():
            walk(ch, depth+1, out)
    except Exception:
        pass
    return out

tree = walk(win)
print(f"Total controls: {len(tree)}")

# Filter: anything mentioning 'bitrate', '250', 'CAN', or a textbox/combo
keywords = ["bit", "rate", "250", "CAN", "can1", "node"]
hits = []
for n in tree:
    name = (n.get("name") or "").lower()
    aid = (n.get("auto_id") or "").lower()
    ct = (n.get("ctrl_type") or "")
    if any(k.lower() in name or k.lower() in aid for k in keywords):
        hits.append(n)
    elif ct in ("ComboBox", "Edit", "Spinner"):
        hits.append(n)

print(f"\nHits ({len(hits)}):")
for h in hits[:80]:
    print(f"  d{h.get('depth')} [{h.get('ctrl_type','?')}] '{h.get('name','')}' aid={h.get('auto_id','')} cls={h.get('class','')}")

# Save full tree for offline inspection
import pathlib
out_path = pathlib.Path("logs/e2e/ui_capture/ui_probe.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nFull tree saved: {out_path}")
