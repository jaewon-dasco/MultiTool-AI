"""Recipe: network_delete <name> — delete a network via UI (similar to device floating toolbar)."""
import sys, time, hashlib, shutil
from pathlib import Path
from . import common

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")

def network_delete(name: str, save: bool = True, backup_dir: Path = None) -> dict:
    result = {"ok": False, "name": name, "before_sha": None, "after_sha": None, "size_delta": None, "log": []}
    def log(msg): result["log"].append(msg); print(f"  [{name}] {msg}")

    if backup_dir:
        backup_dir = Path(backup_dir); backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(PROJ, backup_dir / f"backup_before_delete_{name}.mtproject")

    result["before_sha"] = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
    before_size = PROJ.stat().st_size
    log(f"before sha={result['before_sha']} size={before_size}")

    app, win = common.connect()
    common.ensure_maximized(win)
    common.deselect_diagram(win)

    # Select network
    h = common.find_hyperlink(win, name)
    if not h: log(f"FAIL: hyperlink '{name}' not found"); return result
    h.invoke(); time.sleep(1.2)
    log(f"selected '{name}'")

    # When NETWORK is selected, the floating toolbar appears with different buttons
    # (Events, CSV Editor, Export, Import DBC, Delete) - last one is X (Delete)
    buttons = common.find_floating_toolbar_buttons(win, kind="network")
    if not buttons:
        log("FAIL: no floating toolbar buttons found")
        return result
    log(f"floating toolbar: {len(buttons)} buttons")
    delete_btn = buttons[-1]
    log(f"delete button rect={delete_btn.rectangle()}")
    delete_btn.click_input()
    time.sleep(1)

    # Handle Confirm dialog
    dr = common.dismiss_dialog_if_any(timeout=3, accept=True)
    if dr["handled"]: log(f"dialog '{dr['title']}' -> {dr['button']}")
    else: log("no dialog (silent delete)")

    if save:
        common.save_project(); log("Ctrl+S saved")

    result["after_sha"] = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
    result["size_delta"] = PROJ.stat().st_size - before_size
    log(f"after sha={result['after_sha']} delta={result['size_delta']:+d}")
    result["ok"] = result["before_sha"] != result["after_sha"]
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m skills.e2e_explorer.recipes.network_delete <network>")
        sys.exit(1)
    r = network_delete(sys.argv[1], backup_dir=Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\logs\e2e\recipes\network_delete"))
    delta_str = f"{r['size_delta']:+d}" if r['size_delta'] is not None else "N/A"
    print(f"\nRESULT ok={r['ok']} delta={delta_str}")

if __name__ == "__main__":
    main()
