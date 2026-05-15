#!/usr/bin/env python3
"""End-to-end: change CU_3606_21_1 CAN1 BitRate 250 -> 500, save, diff XML."""
import time, json, hashlib, shutil
from pathlib import Path
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")
OUT = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\logs\e2e\ui_capture")
OUT.mkdir(parents=True, exist_ok=True)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

# Snapshot BEFORE
before_path = OUT / "step1_before.mtproject"
shutil.copy(PROJ, before_path)
before_sha = sha(before_path)
print(f"BEFORE sha={before_sha[:16]} size={before_path.stat().st_size}")

app = Application(backend="uia").connect(title_re=".*MultiTool Creator.*", timeout=10)
win = app.top_window()
win.set_focus()
# Maximize for stable layout
try:
    win.maximize()
except Exception: pass
time.sleep(0.8)

# Find "Bit Rate" label, then find ComboBox on same row (similar y)
label = None
for t in win.descendants(control_type="Text"):
    if t.window_text().strip() == "Bit Rate":
        label = t
        break
if not label:
    print("FAIL: 'Bit Rate' label not found")
    raise SystemExit(1)

lr = label.rectangle()
print(f"Bit Rate label rect: {lr}")

combo = None
best_dx = 99999
for c in win.descendants(control_type="ComboBox"):
    try:
        r = c.rectangle()
        # same row (y overlap) and to the right of label
        if abs((r.top + r.height()//2) - (lr.top + lr.height()//2)) < 15 and r.left > lr.right:
            dx = r.left - lr.right
            if dx < best_dx:
                best_dx = dx
                combo = c
    except Exception: pass

if not combo:
    print("FAIL: BitRate combo not found")
    raise SystemExit(1)

print(f"BitRate combo rect: {combo.rectangle()}")
# Open dropdown
combo.click_input()
time.sleep(1)
win.capture_as_image().save(str(OUT / "bitrate_dropdown.png"))

# Dropdown items may be in a separate popup window OR in desktop scope
from pywinauto import Desktop
desktop = Desktop(backend="uia")
target = None
all_items = []
try:
    # search whole desktop for ListItems in newly-appeared popups
    for it in desktop.windows():
        try:
            for li in it.descendants(control_type="ListItem"):
                all_items.append(li)
        except Exception: pass
except Exception: pass

print(f"ListItems across desktop: {len(all_items)}")
for it in all_items:
    try:
        txt = it.window_text().strip()
        if txt and any(k in txt for k in ["kbit", "125", "250", "500", "1000"]):
            print(f"  candidate: '{txt}'")
            if txt.startswith("500"):
                target = it
    except Exception: pass

if target:
    print(f"Clicking 500: {target.window_text()}")
    target.click_input()
    time.sleep(1)
else:
    # fallback: keyboard nav. ComboBox typically allows arrow keys or type-to-search
    print("Fallback: keyboard '500' + Enter")
    send_keys("500{ENTER}")
    time.sleep(1)

# Save
print("Ctrl+S to save...")
send_keys("^s")
time.sleep(3)

# Some apps show 'Save As' dialog - check for it
try:
    dlg = app.window(title_re=".*Save.*")
    if dlg.exists():
        print("Save dialog detected, pressing Enter")
        send_keys("{ENTER}")
        time.sleep(2)
except Exception: pass

# Snapshot AFTER
after_path = OUT / "step1_after.mtproject"
shutil.copy(PROJ, after_path)
after_sha = sha(after_path)
print(f"AFTER  sha={after_sha[:16]} size={after_path.stat().st_size}")
print(f"CHANGED: {before_sha != after_sha}")

# Quick diff
import re
b_xml = before_path.read_text(encoding="utf-8", errors="replace")
a_xml = after_path.read_text(encoding="utf-8", errors="replace")
# extract BitRate values
for label, xml in [("BEFORE", b_xml), ("AFTER", a_xml)]:
    matches = re.findall(r"<BitRate[^>]*>([^<]+)</BitRate>", xml)
    print(f"{label} BitRate elements: {matches}")
