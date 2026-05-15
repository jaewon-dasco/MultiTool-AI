#!/usr/bin/env python3
"""Click 'Open Project...' hyperlink and load DasDemoProject via file dialog."""
import time
from pywinauto import Application
from pywinauto.keyboard import send_keys

PROJ = r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject"

app = Application(backend="uia").connect(title_re=".*MultiTool Creator.*", timeout=10)
win = app.top_window()
win.set_focus()
time.sleep(0.5)

# Find "Open Project..." hyperlink
open_link = win.descendants(control_type="Hyperlink")
target = None
for h in open_link:
    if "Open Project" in h.window_text():
        target = h
        break

if not target:
    print("FAIL: Open Project hyperlink not found")
    raise SystemExit(1)

print(f"Clicking: {target.window_text()}")
target.invoke() if hasattr(target, "invoke") else target.click_input()
time.sleep(2)

# File dialog should open; type path and Enter
send_keys(PROJ.replace(" ", "{SPACE}"), pause=0.02)
time.sleep(0.5)
send_keys("{ENTER}")
print("Path entered + Enter sent")

# Wait for project load
time.sleep(6)
win = app.top_window()
print(f"Final title: {win.window_text()}")
