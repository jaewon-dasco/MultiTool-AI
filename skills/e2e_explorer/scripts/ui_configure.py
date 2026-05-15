#!/usr/bin/env python3
"""Right-click device or find Configure button → open device CAN tab."""
import time, json, pathlib
from pywinauto import Application
from pywinauto.keyboard import send_keys

app = Application(backend="uia").connect(title_re=".*MultiTool Creator.*", timeout=10)
win = app.top_window()
win.set_focus()
time.sleep(0.3)

# First, ensure CU_3606_21_1 is selected — click its hyperlink in the diagram
hits = [h for h in win.descendants(control_type="Hyperlink") if h.window_text() == "CU_3606_21_1"]
if hits:
    hits[0].invoke()
    time.sleep(1)
    print("Selected CU_3606_21_1")

# Take screenshot of current state
img = win.capture_as_image()
img.save("logs/e2e/ui_capture/before_configure.png")

# Look for any button with tooltip/name containing 'configure' or wrench-like
buttons = win.descendants(control_type="Button")
print(f"Total buttons: {len(buttons)}")
for b in buttons:
    nm = b.window_text() or ""
    aid = b.automation_id() or ""
    if "config" in nm.lower() or "config" in aid.lower() or "wrench" in nm.lower():
        print(f"  HIT [{aid}] '{nm}'")

# Try right-click on the device node hyperlink
print("\nTrying right-click on device hyperlink for context menu...")
if hits:
    rect = hits[0].rectangle()
    print(f"  rect: {rect}")
    try:
        hits[0].right_click_input()
        time.sleep(1)
        # Check for popup menu
        menu_items = win.descendants(control_type="MenuItem")
        print(f"  menu items after right-click: {len(menu_items)}")
        for m in menu_items[:30]:
            nm = m.window_text().strip()
            if nm and nm != "MultiTool.ViewModels.Menu.MenuItem":
                print(f"    '{nm}'")
        # Save screenshot
        win.capture_as_image().save("logs/e2e/ui_capture/after_rightclick.png")
        # Close menu
        send_keys("{ESC}")
    except Exception as e:
        print(f"  right-click err: {e}")
