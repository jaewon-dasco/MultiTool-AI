"""Recipe: device_disconnect <network> <device> — remove device from network via Network Properties X button."""
import sys, time, hashlib, shutil
from pathlib import Path
from . import common

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")

def device_disconnect_from_network(network: str, device: str, save: bool = True, backup_dir: Path = None) -> dict:
    """Remove a device from a network using the small X button next to device name in Network Properties panel."""
    result = {"ok": False, "network": network, "device": device, "before_sha": None, "after_sha": None, "size_delta": None, "log": []}
    def log(msg): result["log"].append(msg); print(f"  [{network}/{device}] {msg}")

    if backup_dir:
        backup_dir = Path(backup_dir); backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(PROJ, backup_dir / f"backup_before_disconnect_{network}_{device}.mtproject")

    result["before_sha"] = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
    before_size = PROJ.stat().st_size
    log(f"before sha={result['before_sha']} size={before_size}")

    app, win = common.connect()
    common.ensure_maximized(win)
    common.deselect_diagram(win)

    # Select network to bring up Network Properties panel
    h = common.find_hyperlink(win, network)
    if not h: log(f"FAIL: network hyperlink '{network}' not found"); return result
    h.invoke(); time.sleep(1.2)
    log(f"selected network '{network}'")

    # Find the "Devices" label in left panel (x < 250)
    devices_label = None
    for t in win.descendants(control_type="Text"):
        if t.window_text().strip() == "Devices":
            r = t.rectangle()
            if r.left < 250:
                devices_label = t; break
    if not devices_label: log("FAIL: Devices label not found"); return result
    dl_rect = devices_label.rectangle()
    log(f"Devices label at {dl_rect}")

    # Find small X buttons (14x14) below the Devices label in the left panel
    candidates = []
    for b in win.descendants(control_type="Button"):
        try:
            r = b.rectangle()
            if (13 <= r.width() <= 15 and 13 <= r.height() <= 15
                and r.left < 250 and r.top > dl_rect.bottom and b.window_text() == ""
                and not b.automation_id()):
                candidates.append(b)
        except: pass
    candidates.sort(key=lambda b: b.rectangle().top)
    log(f"X-button candidates in Devices list: {len(candidates)}")

    if not candidates:
        log("FAIL: no X buttons in Devices list")
        return result

    # Device order in panel == order shown to user; if multiple devices match, must pick by index.
    # For now: find via positional match against device name text in left panel.
    # Devices list shows entries like "<nodeid> <DeviceName>" — locate the row containing 'device' text.
    name_texts = []
    for t in win.descendants(control_type="Text"):
        if device in (t.window_text() or "").strip():
            r = t.rectangle()
            if r.left < 250 and r.top > dl_rect.bottom:
                name_texts.append(t)
    log(f"device name texts matching '{device}': {len(name_texts)}")
    if not name_texts:
        log(f"FAIL: device '{device}' not found in Devices list")
        return result
    target_text = name_texts[0]
    tt_rect = target_text.rectangle()
    # Find the X button on the same row
    target_x = None; best_dx = 99999
    for b in candidates:
        br = b.rectangle()
        if abs((br.top + br.height()//2) - (tt_rect.top + tt_rect.height()//2)) < 12:
            dx = abs(br.left - tt_rect.right)
            if dx < best_dx: best_dx = dx; target_x = b
    if not target_x:
        log("FAIL: no X button on device row, picking first")
        target_x = candidates[0]
    log(f"clicking X at {target_x.rectangle()}")
    target_x.click_input()
    time.sleep(1.5)

    # Some MultiTool versions show a confirm dialog for disconnect, others silent
    dr = common.dismiss_dialog_if_any(timeout=2, accept=True)
    if dr["handled"]: log(f"dialog '{dr['title']}' -> {dr['button']}")
    else: log("no dialog (silent disconnect)")

    if save:
        common.save_project(); log("Ctrl+S saved")

    result["after_sha"] = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
    result["size_delta"] = PROJ.stat().st_size - before_size
    log(f"after sha={result['after_sha']} delta={result['size_delta']:+d}")
    result["ok"] = result["before_sha"] != result["after_sha"]
    return result


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m skills.e2e_explorer.recipes.device_disconnect <network> <device>")
        sys.exit(1)
    r = device_disconnect_from_network(sys.argv[1], sys.argv[2], backup_dir=Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\logs\e2e\recipes\device_disconnect"))
    delta_str = f"{r['size_delta']:+d}" if r['size_delta'] is not None else "N/A"
    print(f"\nRESULT ok={r['ok']} delta={delta_str}")

if __name__ == "__main__":
    main()
