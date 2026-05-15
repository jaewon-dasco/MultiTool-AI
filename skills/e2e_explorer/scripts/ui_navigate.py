#!/usr/bin/env python3
"""Navigate: click CU_3606_21_1 hyperlink to open device editor."""
import sys, time, json, pathlib
from pywinauto import Application

target_name = sys.argv[1] if len(sys.argv) > 1 else "CU_3606_21_1"

app = Application(backend="uia").connect(title_re=".*MultiTool Creator.*", timeout=10)
win = app.top_window()
win.set_focus()
time.sleep(0.3)

# Find hyperlink by name
hits = []
for h in win.descendants(control_type="Hyperlink"):
    if h.window_text() == target_name:
        hits.append(h)
print(f"Hyperlinks matching '{target_name}': {len(hits)}")

if not hits:
    raise SystemExit("not found")

target = hits[0]
print(f"Clicking via invoke: {target.window_text()}")
try:
    target.invoke()
except Exception as e:
    print(f"invoke failed ({e}); try click_input")
    target.click_input(double=True)

time.sleep(2)

# Re-probe — count controls
def walk(c, d=0, out=None):
    if out is None: out=[]
    try:
        out.append({"d":d,"ct":c.element_info.control_type,"n":c.window_text()[:60],"aid":c.automation_id() or "","cls":c.class_name()})
    except Exception:
        return out
    if d>25: return out
    try:
        for ch in c.children(): walk(ch,d+1,out)
    except Exception: pass
    return out

tree = walk(win)
print(f"Controls after click: {len(tree)}")

# Find BitRate / numeric fields / new tabs
for n in tree:
    nm = n["n"].strip()
    aid = n["aid"]
    ct = n["ct"]
    if ("bit" in nm.lower() or "bit" in aid.lower() or "rate" in nm.lower() or
        "250" in nm or "500" in nm or "node" in nm.lower() or "node" in aid.lower() or
        ct == "TabItem" or
        (ct == "ComboBox" and aid)):
        print(f"d{n['d']:2} [{ct:11}] '{nm}' aid={aid[:40]} cls={n['cls']}")

pathlib.Path("logs/e2e/ui_capture/ui_after_nav.json").write_text(
    json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
