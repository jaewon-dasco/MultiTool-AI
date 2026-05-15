"""Recipe: network_bitrate_change <network_name> <bitrate> — change network BitRate via UI."""
import sys, time, hashlib, shutil
from pathlib import Path
from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys
from . import common

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")

def network_bitrate_change(network_name: str, new_bitrate: str, save: bool = True, backup_dir: Path = None) -> dict:
    """Change BitRate for the given network via UI."""
    result = {"ok": False, "network": network_name, "bitrate": new_bitrate, "before_sha": None, "after_sha": None, "size_delta": None, "log": []}
    def log(msg): result["log"].append(msg); print(f"  [{network_name}] {msg}")

    if backup_dir:
        backup_dir = Path(backup_dir); backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(PROJ, backup_dir / f"backup_before_bitrate_{network_name}_{new_bitrate}.mtproject")

    result["before_sha"] = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
    before_size = PROJ.stat().st_size
    log(f"before sha={result['before_sha']} size={before_size}")

    app, win = common.connect()
    common.ensure_maximized(win)
    common.deselect_diagram(win)

    # Click network hyperlink in left tree / diagram
    h = common.find_hyperlink(win, network_name)
    if not h: log(f"FAIL: hyperlink '{network_name}' not found"); return result
    h.invoke(); time.sleep(1.2)
    log(f"selected '{network_name}'")

    # Find Bit Rate label in left Network Properties panel + adjacent ComboBox
    label = next((t for t in win.descendants(control_type="Text") if t.window_text().strip() == "Bit Rate"), None)
    if not label: log("FAIL: Bit Rate label not found"); return result
    lr = label.rectangle()
    combo = None; best_dy = 99999
    for c in win.descendants(control_type="ComboBox"):
        try:
            r = c.rectangle()
            # Network Properties panel: combo BELOW label (vertical stack), x<250
            if r.left < 250 and r.top > lr.top and (r.top - lr.bottom) < 30:
                dy = r.top - lr.bottom
                if dy < best_dy: best_dy = dy; combo = c
        except: pass
    if not combo: log("FAIL: BitRate combo not found"); return result
    if not combo.is_enabled(): log("FAIL: combo disabled"); return result
    log(f"combo rect={combo.rectangle()} enabled=True")

    combo.click_input(); time.sleep(1)

    # Pick the matching option from dropdown (desktop scope)
    target = None
    for w in Desktop(backend="uia").windows():
        try:
            for li in w.descendants(control_type="ListItem"):
                txt = li.window_text().strip()
                if txt.startswith(new_bitrate):
                    target = li; break
            if target: break
        except: pass
    if target:
        target.click_input(); time.sleep(1)
        log(f"selected {target.window_text()!r}")
    else:
        send_keys(f"{new_bitrate}{{ENTER}}"); time.sleep(1)
        log(f"fallback keys '{new_bitrate}'+Enter")

    # Click away to commit focus
    try:
        name_lbl = next((t for t in win.descendants(control_type="Text") if t.window_text().strip() == "Name"), None)
        if name_lbl: name_lbl.click_input()
    except: pass
    time.sleep(0.4)

    if save:
        common.save_project()
        log("Ctrl+S saved")

    result["after_sha"] = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
    result["size_delta"] = PROJ.stat().st_size - before_size
    log(f"after sha={result['after_sha']} delta={result['size_delta']:+d}")
    result["ok"] = result["before_sha"] != result["after_sha"]
    return result


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m skills.e2e_explorer.recipes.network_bitrate <network> <bitrate>")
        sys.exit(1)
    r = network_bitrate_change(sys.argv[1], sys.argv[2], backup_dir=Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\logs\e2e\recipes\network_bitrate"))
    delta_str = f"{r['size_delta']:+d}" if r['size_delta'] is not None else "N/A"
    print(f"\nRESULT ok={r['ok']} delta={delta_str}")

if __name__ == "__main__":
    main()
