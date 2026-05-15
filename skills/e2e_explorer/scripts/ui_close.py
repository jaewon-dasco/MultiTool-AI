#!/usr/bin/env python3
"""Close MultiTool gracefully via Alt+F4. Handles unsaved-changes dialog."""
import sys, time
from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys

# Mode: --discard (don't save) | --save (save) | --cancel
mode = sys.argv[1] if len(sys.argv) > 1 else "--discard"

try:
    app = Application(backend="uia").connect(title_re=".*MultiTool Creator.*", timeout=5)
except Exception:
    print("MultiTool not running — nothing to do")
    sys.exit(0)

win = app.top_window()
win.set_focus()
time.sleep(0.3)
print(f"Closing: {win.window_text()}")
send_keys("%{F4}")
time.sleep(1.5)

# Check for "Save changes?" dialog at top-level
dlg = None
for w in Desktop(backend="uia").windows():
    try:
        title = w.window_text() or ""
        if "MultiTool" in title and w.element_info.control_type == "Window" and w != win:
            dlg = w; break
        # heuristic: small modal with Yes/No/Cancel buttons
        btns = [b.window_text() for b in w.descendants(control_type="Button") if b.window_text()]
        if any(b in ("Yes","No","Cancel","Save","Don't Save") for b in btns):
            dlg = w; break
    except Exception: pass

if dlg:
    print(f"Save dialog: {dlg.window_text()!r}")
    buttons = {b.window_text(): b for b in dlg.descendants(control_type="Button") if b.window_text()}
    print(f"  buttons: {list(buttons.keys())}")
    pick = None
    if mode == "--discard":
        for k in ("Don't Save", "No", "Discard"):
            if k in buttons: pick = buttons[k]; break
    elif mode == "--save":
        for k in ("Save", "Yes"):
            if k in buttons: pick = buttons[k]; break
    else:
        for k in ("Cancel",):
            if k in buttons: pick = buttons[k]; break
    if pick:
        print(f"  clicking: {pick.window_text()!r}")
        pick.invoke() if hasattr(pick, "invoke") else pick.click_input()
    else:
        # Fallback to keystroke: N for No / S for Save
        key = "n" if mode == "--discard" else "s" if mode == "--save" else "{ESC}"
        print(f"  fallback keystroke: {key}")
        send_keys(key)
    time.sleep(2)

# Verify gone
import subprocess
res = subprocess.run(["powershell", "-Command", "(Get-Process MultiTool -ErrorAction SilentlyContinue) | Measure-Object | Select-Object -ExpandProperty Count"], capture_output=True, text=True)
print(f"MultiTool processes remaining: {res.stdout.strip()}")
