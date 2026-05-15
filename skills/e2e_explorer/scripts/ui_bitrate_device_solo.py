#!/usr/bin/env python3
"""Solo-device BitRate change (after network disconnect): 250 -> 500 + save + diff."""
import time, hashlib, shutil, re, difflib
from pathlib import Path
from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")
OUT = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\logs\e2e\ui_capture")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

before_path = OUT / "solo_before.mtproject"
shutil.copy(PROJ, before_path)
before_sha = sha(before_path)
print(f"BEFORE sha={before_sha[:16]} size={before_path.stat().st_size}")

app = Application(backend="uia").connect(title_re=".*MultiTool Creator.*", timeout=10)
win = app.top_window()
win.set_focus(); time.sleep(0.5)

# Already on Configure (Device CAN tab) per prior step. Find BitRate combo.
label = next((t for t in win.descendants(control_type="Text") if t.window_text().strip() == "Bit Rate"), None)
if not label: raise SystemExit("Bit Rate label not found")
lr = label.rectangle()
combo = None
for c in win.descendants(control_type="ComboBox"):
    try:
        r = c.rectangle()
        if abs((r.top + r.height()//2) - (lr.top + lr.height()//2)) < 15 and r.left > lr.right:
            combo = c; break
    except: pass
if not combo: raise SystemExit("BitRate combo not found")
print(f"Combo rect={combo.rectangle()} enabled={combo.is_enabled()}")
if not combo.is_enabled(): raise SystemExit("ABORT: combo disabled")

# Open and pick 500
combo.click_input(); time.sleep(1)
target = None
for w in Desktop(backend="uia").windows():
    try:
        for li in w.descendants(control_type="ListItem"):
            if li.window_text().strip().startswith("500"):
                target = li; break
        if target: break
    except: pass
if target:
    target.click_input(); time.sleep(1)
    print("Selected 500")
else:
    send_keys("500{ENTER}"); time.sleep(1)
    print("Fallback keystrokes")

# Commit focus
try:
    name_lbl = next((t for t in win.descendants(control_type="Text") if t.window_text().strip() == "Device Name"), None)
    if name_lbl: name_lbl.click_input()
except: pass
time.sleep(0.4)

# Save
send_keys("^s"); time.sleep(3)

# After snapshot + diff
shutil.copy(PROJ, OUT / "solo_after.mtproject")
after_path = OUT / "solo_after.mtproject"
after_sha = sha(after_path)
print(f"AFTER  sha={after_sha[:16]} size={after_path.stat().st_size}")
print(f"CHANGED: {before_sha != after_sha}")

for tag, p in [("BEFORE", before_path), ("AFTER", after_path)]:
    xml = p.read_text(encoding="utf-8", errors="replace")
    big = re.findall(r"<BitRate[^>]*>([^<]+)</BitRate>", xml)
    small = re.findall(r"<Bitrate[^>]*>([^<]+)</Bitrate>", xml)
    print(f"{tag} <BitRate>={big} <Bitrate>={small}")

b = before_path.read_text(encoding="utf-8", errors="replace").splitlines()
a = after_path.read_text(encoding="utf-8", errors="replace").splitlines()
diff = list(difflib.unified_diff(b, a, n=0, lineterm=""))
changed = [ln for ln in diff if ln.startswith(('+','-')) and not ln.startswith(('+++','---'))]
print(f"Changed lines: {len(changed)}")
for ln in changed[:30]:
    print(ln.encode('ascii','replace').decode('ascii')[:200])
(OUT / "solo_diff.txt").write_text("\n".join(diff), encoding="utf-8")
print(f"Full diff: {OUT/'solo_diff.txt'}")
