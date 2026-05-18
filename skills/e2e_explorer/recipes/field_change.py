"""Generic recipe: navigate device → Configure → tab → field, set value, save.

Powers UI-channel learning for all CAN Settings · J1939 · Diagnostics · IO · OD · CodesysConfig · PDO fields.
"""
import sys, time, hashlib, shutil, json, re
from pathlib import Path
from pywinauto import Application, Desktop, mouse
from pywinauto.keyboard import send_keys
from . import common

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")


def open_configure_panel(win, device_name: str) -> bool:
    """Select device → click wrench (Configure) → tabs panel opens."""
    common.deselect_diagram(win)
    h = common.find_hyperlink(win, device_name)
    if not h: return False
    h.invoke()
    time.sleep(1.2)
    buttons = common.find_floating_toolbar_buttons(win, kind="device")
    if len(buttons) < 3: return False
    # Leftmost = wrench (Configure)
    wrench = buttons[0]
    wrench.click_input()
    time.sleep(2)
    return True


def click_left_tab(win, tab_name: str) -> bool:
    """Configure 패널 좌측 메뉴(CAN/J1939/.../Object Dictionary/IO 등)에서 탭 클릭.
    Tab은 보통 Text element로 노출됨."""
    # Search Text elements in left margin (x < 200) that match name
    for t in win.descendants(control_type="Text"):
        try:
            r = t.rectangle()
            if r.left < 200 and t.window_text().strip() == tab_name:
                t.click_input()
                time.sleep(1.5)
                return True
        except Exception: pass
    return False


def find_field_combo_or_edit(win, label_text: str, x_lt: int = 1500):
    """Find ComboBox/Edit adjacent to a Text label.
    Returns (control, kind) or (None, None).
    kind: 'combo' | 'edit' | 'checkbox'
    """
    label = None
    for t in win.descendants(control_type="Text"):
        if t.window_text().strip() == label_text:
            label = t; break
    if not label: return None, None
    lr = label.rectangle()
    best = None; best_dist = 99999; kind = None
    # Same-row to right (horizontal layout)
    for c in win.descendants(control_type="ComboBox"):
        try:
            r = c.rectangle()
            if abs((r.top + r.height()//2) - (lr.top + lr.height()//2)) < 18 and r.left > lr.right and r.left < x_lt:
                d = r.left - lr.right
                if d < best_dist: best_dist = d; best = c; kind = "combo"
        except Exception: pass
    for c in win.descendants(control_type="Edit"):
        try:
            r = c.rectangle()
            if abs((r.top + r.height()//2) - (lr.top + lr.height()//2)) < 18 and r.left > lr.right and r.left < x_lt:
                d = r.left - lr.right
                if d < best_dist: best_dist = d; best = c; kind = "edit"
        except Exception: pass
    for c in win.descendants(control_type="CheckBox"):
        try:
            r = c.rectangle()
            if abs((r.top + r.height()//2) - (lr.top + lr.height()//2)) < 18 and r.left > lr.right and r.left < x_lt:
                d = r.left - lr.right
                if d < best_dist: best_dist = d; best = c; kind = "checkbox"
        except Exception: pass
    # Vertical layout fallback (label above input)
    if best is None:
        for c in win.descendants(control_type="ComboBox"):
            try:
                r = c.rectangle()
                if r.top > lr.bottom and (r.top - lr.bottom) < 30 and abs(r.left - lr.left) < 30:
                    d = r.top - lr.bottom
                    if d < best_dist: best_dist = d; best = c; kind = "combo"
            except Exception: pass
    return best, kind


def select_combo_value(win, combo, value: str) -> bool:
    """Open combo, pick matching ListItem from desktop scope, fallback to keystrokes."""
    combo.click_input()
    time.sleep(1)
    target = None
    for w in Desktop(backend="uia").windows():
        try:
            for li in w.descendants(control_type="ListItem"):
                if li.window_text().strip().lower() == value.lower() or li.window_text().strip().startswith(value):
                    target = li; break
            if target: break
        except Exception: pass
    if target:
        target.click_input()
        time.sleep(1)
        return True
    # Fallback: type-search
    send_keys(value + "{ENTER}")
    time.sleep(1)
    return False


def set_edit_value(edit, value: str) -> None:
    edit.set_focus()
    time.sleep(0.2)
    send_keys("^a")
    time.sleep(0.1)
    send_keys("{DELETE}")
    time.sleep(0.1)
    send_keys(value)
    time.sleep(0.2)
    send_keys("{TAB}")
    time.sleep(0.4)


def toggle_checkbox(cb, desired: bool) -> None:
    try:
        is_checked = cb.get_toggle_state() == 1
    except Exception:
        is_checked = None
    if is_checked is None or is_checked != desired:
        cb.click_input()
        time.sleep(0.4)


def change_field(device_name: str, tab_name: str, label: str, value: str,
                 field_kind_hint: str | None = None, save: bool = True,
                 backup_dir: Path | None = None) -> dict:
    """End-to-end: open device Configure, switch tab, change label's adjacent control, save."""
    result = {"ok": False, "label": label, "value": value, "before_sha": None, "after_sha": None,
              "size_delta": None, "kind": None, "log": []}
    def log(msg): result["log"].append(msg); print(f"  [{label}={value}] {msg}")

    if backup_dir:
        backup_dir = Path(backup_dir); backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(PROJ, backup_dir / f"backup_before_{label}_{value}.mtproject")

    result["before_sha"] = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
    before_size = PROJ.stat().st_size
    log(f"before sha={result['before_sha']} size={before_size}")

    app, win = common.connect()
    common.ensure_maximized(win)

    if not open_configure_panel(win, device_name):
        log("FAIL: Configure panel did not open"); return result
    log("Configure panel opened")

    if tab_name:
        if not click_left_tab(win, tab_name):
            log(f"FAIL: tab '{tab_name}' not found"); return result
        log(f"tab '{tab_name}' selected")

    ctrl, kind = find_field_combo_or_edit(win, label)
    if not ctrl:
        log(f"FAIL: field '{label}' not found"); return result
    result["kind"] = kind
    log(f"field kind={kind} rect={ctrl.rectangle()}")
    if not ctrl.is_enabled():
        log("FAIL: control disabled"); return result

    if kind == "combo":
        select_combo_value(win, ctrl, value)
    elif kind == "edit":
        set_edit_value(ctrl, value)
    elif kind == "checkbox":
        desired = value.lower() in ("true", "1", "yes", "on")
        toggle_checkbox(ctrl, desired)

    time.sleep(0.5)
    if save:
        common.save_project()
        log("saved")

    result["after_sha"] = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
    result["size_delta"] = PROJ.stat().st_size - before_size
    log(f"after sha={result['after_sha']} delta={result['size_delta']:+d}")
    result["ok"] = result["before_sha"] != result["after_sha"]
    return result


def main():
    if len(sys.argv) < 5:
        print("Usage: python -m skills.e2e_explorer.recipes.field_change <device> <tab> <label> <value>")
        sys.exit(1)
    bk = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\logs\e2e\recipes\field_change")
    r = change_field(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], backup_dir=bk)
    print(f"\nRESULT ok={r['ok']} delta={r['size_delta']!s} kind={r['kind']}")


if __name__ == "__main__":
    main()
