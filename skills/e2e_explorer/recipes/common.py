"""Shared helpers for MultiTool UI recipes."""
import time
from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys

def connect(timeout=10):
    app = Application(backend="uia").connect(title_re=".*MultiTool Creator.*", timeout=timeout)
    win = app.top_window()
    win.set_focus()
    time.sleep(0.3)
    return app, win

def ensure_maximized(win):
    try: win.maximize()
    except Exception: pass
    time.sleep(0.5)

def find_hyperlink(win, name):
    for h in win.descendants(control_type="Hyperlink"):
        if h.window_text() == name:
            return h
    return None

def deselect_diagram(win):
    """Click empty canvas area to deselect any selected device.
    Required before searching for device hyperlinks (which disappear from tree when a device is selected)."""
    from pywinauto import mouse
    r = win.rectangle()
    # Empty canvas: right-middle area of the window
    x = r.left + int(r.width() * 0.75)
    y = r.top + int(r.height() * 0.75)
    mouse.click(button="left", coords=(x, y))
    time.sleep(0.8)

def find_floating_toolbar_buttons(win, min_x=300):
    """Find the 3 small unnamed buttons of the device floating toolbar.
    Returns list sorted by left coordinate (wrench, cube, X order).
    """
    out = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            if 25 <= r.width() <= 32 and 25 <= r.height() <= 32 and r.left > min_x and b.window_text() == "" and not b.automation_id():
                out.append(b)
        except Exception: pass
    out.sort(key=lambda b: b.rectangle().left)
    return out

def save_project():
    send_keys("^s")
    time.sleep(2.5)

def dismiss_dialog_if_any(timeout=3, accept=True):
    """Detect WPF MessageBox via win32 backend (UIA doesn't see them as separate windows).
    accept=True → click Yes/OK; False → click No/Cancel.
    Returns dict {handled, title, button} or {handled: False}.
    """
    from pywinauto import mouse
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            for w in Desktop(backend="win32").windows():
                try:
                    title = w.window_text() or ""
                    cls = w.class_name() or ""
                    if title in ("Confirm",) or (title and "HwndWrapper[MultiTool" in cls):
                        if title != "Confirm": continue
                        r = w.rectangle()
                        # Heuristic: Yes button ~145px from right, Cancel ~30px
                        if accept:
                            x = r.right - 145; btn = "Yes"
                        else:
                            x = r.right - 30; btn = "Cancel"
                        y = r.bottom - 25
                        mouse.click(coords=(x, y))
                        time.sleep(1.5)
                        return {"handled": True, "title": title, "button": btn, "coords": (x,y)}
                except Exception: pass
        except Exception: pass
        time.sleep(0.3)
    return {"handled": False}
