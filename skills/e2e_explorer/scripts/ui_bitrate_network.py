#!/usr/bin/env python3
"""Network-level BitRate change end-to-end: 250 -> 500, save, XML diff."""
import time, json, hashlib, shutil, re, difflib
from pathlib import Path
from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")
OUT = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\logs\e2e\ui_capture")
OUT.mkdir(parents=True, exist_ok=True)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

# Fresh backup just in case
shutil.copy(PROJ, OUT / "net1_before.mtproject")
before_path = OUT / "net1_before.mtproject"
before_sha = sha(before_path)
print(f"BEFORE sha={before_sha[:16]} size={before_path.stat().st_size}")

app = Application(backend="uia").connect(title_re=".*MultiTool Creator.*", timeout=10)
win = app.top_window()
win.set_focus()
try: win.maximize()
except: pass
time.sleep(0.5)

# Ensure NETWORK1 selected
hits = [h for h in win.descendants(control_type="Hyperlink") if h.window_text() == "NETWORK1"]
if hits:
    hits[0].invoke(); time.sleep(1)

# Find "Bit Rate" label, then ComboBox in same row
label = None
for t in win.descendants(control_type="Text"):
    if t.window_text().strip() == "Bit Rate":
        label = t; break
if not label: raise SystemExit("Bit Rate label not found")
lr = label.rectangle()
print(f"Bit Rate label rect: {lr}")

combo = None; best_dy = 99999
for c in win.descendants(control_type="ComboBox"):
    try:
        r = c.rectangle()
        # Network Properties panel: combo is BELOW the label (vertical stack), not horizontal
        if r.left < 250 and r.top > lr.top and (r.top - lr.bottom) < 30:
            dy = r.top - lr.bottom
            if dy < best_dy:
                best_dy = dy; combo = c
    except: pass
if not combo: raise SystemExit("BitRate combo not found")

print(f"BitRate combo rect: {combo.rectangle()}")
print(f"  enabled: {combo.is_enabled()}")
if not combo.is_enabled():
    raise SystemExit("FAIL: ComboBox is DISABLED — aborting")

# Open dropdown
combo.click_input()
time.sleep(1)
win.capture_as_image().save(str(OUT / "net1_dropdown.png"))

# Find 500 option (across desktop, since popup may be top-level)
target = None
for w in Desktop(backend="uia").windows():
    try:
        for li in w.descendants(control_type="ListItem"):
            txt = li.window_text().strip()
            if txt.startswith("500"):
                target = li; print(f"  found option: '{txt}'"); break
        if target: break
    except: pass

if target:
    target.click_input()
    time.sleep(1)
    print("Selected 500 via click")
else:
    print("Fallback: keyboard '5' to type-search")
    send_keys("500{ENTER}")
    time.sleep(1)

# Click away from combo to commit value (focus elsewhere)
try:
    name_label = next((t for t in win.descendants(control_type="Text") if t.window_text().strip() == "Name"), None)
    if name_label: name_label.click_input()
except: pass
time.sleep(0.5)

# Save
print("Ctrl+S...")
send_keys("^s")
time.sleep(3)

# Snapshot AFTER
shutil.copy(PROJ, OUT / "net1_after.mtproject")
after_path = OUT / "net1_after.mtproject"
after_sha = sha(after_path)
print(f"AFTER  sha={after_sha[:16]} size={after_path.stat().st_size}")
print(f"CHANGED: {before_sha != after_sha}")

# Inspect BitRate elements
for label_, p in [("BEFORE", before_path), ("AFTER", after_path)]:
    xml = p.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(r"<BitRate[^>]*>([^<]+)</BitRate>", xml)
    print(f"{label_} <BitRate>: {matches}")

# Compute compact diff (changed lines only)
b = before_path.read_text(encoding="utf-8", errors="replace").splitlines()
a = after_path.read_text(encoding="utf-8", errors="replace").splitlines()
diff = list(difflib.unified_diff(b, a, n=0, lineterm=""))
changed = [ln for ln in diff if ln.startswith(('+','-')) and not ln.startswith(('+++','---'))]
print(f"\nChanged line count: {len(changed)}")
print("--- first 20 changed lines ---")
for ln in changed[:20]:
    # strip non-ascii for stdout safety
    print(ln.encode('ascii','replace').decode('ascii')[:200])

# Save diff
(OUT / "net1_diff.txt").write_text("\n".join(diff), encoding="utf-8")
print(f"\nFull diff saved: {OUT / 'net1_diff.txt'}")
