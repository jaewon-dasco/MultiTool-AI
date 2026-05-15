"""Recipe: device_delete <name> — delete a device via UI floating toolbar."""
import sys, time, hashlib, shutil
from pathlib import Path
from . import common

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")

def device_delete(name: str, save: bool = True, backup_dir: Path = None) -> dict:
    """Delete a device by name via MultiTool UI.

    Returns dict with: ok, name, before_sha, after_sha, size_delta.
    """
    result = {"ok": False, "name": name, "before_sha": None, "after_sha": None, "size_delta": None, "log": []}

    def log(msg): result["log"].append(msg); print(f"  [{name}] {msg}")

    # Backup
    if backup_dir:
        backup_dir = Path(backup_dir); backup_dir.mkdir(parents=True, exist_ok=True)
        bk = backup_dir / f"backup_before_delete_{name}.mtproject"
        shutil.copy(PROJ, bk)
        log(f"backup -> {bk}")

    result["before_sha"] = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
    before_size = PROJ.stat().st_size
    log(f"before sha={result['before_sha']} size={before_size}")

    app, win = common.connect()
    common.ensure_maximized(win)

    # Step 0: Deselect any prior selection so device hyperlinks are visible
    common.deselect_diagram(win)

    # Step 1: Select device
    h = common.find_hyperlink(win, name)
    if not h:
        log(f"FAIL: device hyperlink '{name}' not found")
        return result
    h.invoke()
    time.sleep(1.2)
    log(f"selected '{name}'")

    # Step 2: Find floating toolbar
    buttons = common.find_floating_toolbar_buttons(win)
    if len(buttons) < 3:
        log(f"FAIL: expected 3 floating buttons, got {len(buttons)}")
        return result
    log(f"floating toolbar: {len(buttons)} buttons")
    # Rightmost is X (delete)
    delete_btn = buttons[-1]
    log(f"delete button rect={delete_btn.rectangle()}")

    # Step 3: Click delete
    delete_btn.click_input()
    time.sleep(1)

    # Step 4: Confirm dialog (WPF MessageBox - only visible via win32 backend)
    dr = common.dismiss_dialog_if_any(timeout=3, accept=True)
    if dr["handled"]: log(f"dialog '{dr['title']}' -> {dr['button']} at {dr['coords']}")
    else: log("no dialog appeared (silent delete)")

    # Step 5: Save
    if save:
        common.save_project()
        log("Ctrl+S saved")

    result["after_sha"] = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
    after_size = PROJ.stat().st_size
    result["size_delta"] = after_size - before_size
    log(f"after sha={result['after_sha']} size={after_size} delta={result['size_delta']:+d}")
    result["ok"] = result["before_sha"] != result["after_sha"]
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m skills.e2e_explorer.recipes.device_delete <device_name>")
        sys.exit(1)
    name = sys.argv[1]
    backup_dir = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\logs\e2e\recipes\device_delete")
    r = device_delete(name, save=True, backup_dir=backup_dir)
    print()
    delta_str = f"{r['size_delta']:+d}" if r['size_delta'] is not None else "N/A"
    print(f"RESULT ok={r['ok']} delta={delta_str}")

if __name__ == "__main__":
    main()
