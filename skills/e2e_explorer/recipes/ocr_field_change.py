"""OCR-based field change: screenshot → winocr → keyword search → coord click.

Bypasses UI Automation limitations for WPF Telerik controls in MultiTool's Configure panel.
"""
import sys, time, hashlib, shutil, json
from pathlib import Path
from PIL import ImageGrab
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys
import winocr
from . import common

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")


def ocr_screen() -> list[dict]:
    """Capture full screen + run Windows OCR. Returns list of {text, x, y, w, h}.
    Coordinates are screen-absolute."""
    img = ImageGrab.grab()
    result = winocr.recognize_pil_sync(img, lang="en-US")
    out = []
    for line in result.get("lines", []):
        text = line.get("text", "")
        # use bounding rect of full line (first+last word combined)
        words = line.get("words", [])
        if not words: continue
        # union bounding box
        xs = [w["bounding_rect"]["x"] for w in words]
        ys = [w["bounding_rect"]["y"] for w in words]
        xe = [w["bounding_rect"]["x"] + w["bounding_rect"]["width"] for w in words]
        ye = [w["bounding_rect"]["y"] + w["bounding_rect"]["height"] for w in words]
        out.append({"text": text, "x": int(min(xs)), "y": int(min(ys)),
                    "w": int(max(xe) - min(xs)), "h": int(max(ye) - min(ys))})
    return out


def find_label_coords(ocr_lines: list[dict], label: str, fuzzy: bool = True):
    """Return (x_center, y_center, right_edge, bottom_edge) of label box, or None.
    fuzzy: case-insensitive substring match for label keyword(s)."""
    label_norm = label.lower()
    candidates = []
    for ln in ocr_lines:
        t = ln["text"].lower()
        if fuzzy:
            # fuzzy substring or near-match
            if label_norm in t or all(w in t for w in label_norm.split()):
                candidates.append(ln)
        else:
            if t == label_norm: candidates.append(ln)
    if not candidates: return None
    # prefer shortest text (= exact label not surrounding sentence)
    candidates.sort(key=lambda c: len(c["text"]))
    c = candidates[0]
    return c["x"] + c["w"]//2, c["y"] + c["h"]//2, c["x"] + c["w"], c["y"] + c["h"]


def click_input_right_of_label(ocr_lines: list[dict], label: str, offset_x: int = 100, retry: int = 0) -> bool:
    """Click ~offset_x pixels to the right of the label's right edge (typical input position)."""
    coords = find_label_coords(ocr_lines, label)
    if not coords:
        return False
    _, y_center, right_edge, _ = coords
    click_x = right_edge + offset_x
    click_y = y_center
    mouse.click(coords=(click_x, click_y))
    time.sleep(0.4)
    return True


def change_numeric_field(label: str, value: str, offset_x: int = 100) -> bool:
    """Click input next to label, clear, type new value, Tab to commit."""
    ocr_lines = ocr_screen()
    coords = find_label_coords(ocr_lines, label)
    if not coords:
        return False
    _, y_center, right_edge, _ = coords
    # numeric input box typically starts ~50-100px right of label right-edge
    click_x = right_edge + offset_x
    click_y = y_center
    mouse.click(coords=(click_x, click_y))
    time.sleep(0.3)
    send_keys("^a"); time.sleep(0.1)
    send_keys("{DELETE}"); time.sleep(0.1)
    send_keys(value); time.sleep(0.2)
    send_keys("{TAB}"); time.sleep(0.4)
    return True


def run_field_change(device_name: str, sidebar_tab: str | None, label: str, value: str,
                     save: bool = True, backup_dir: Path | None = None) -> dict:
    result = {"ok": False, "label": label, "value": value, "before_sha": None,
              "after_sha": None, "size_delta": None, "log": []}
    def log(msg): result["log"].append(msg); print(f"  [{label}={value}] {msg}")

    if backup_dir:
        backup_dir = Path(backup_dir); backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(PROJ, backup_dir / f"backup_before_{label.replace('/','_').replace(' ','_')}_{value}.mtproject")

    result["before_sha"] = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
    log(f"before sha={result['before_sha']}")

    app, win = common.connect()
    common.ensure_maximized(win)

    # 1. Open Configure
    from .field_change import open_configure_panel
    if not open_configure_panel(win, device_name):
        log("FAIL: Configure panel"); return result
    log("Configure opened")

    # 2. Switch sidebar tab if requested (CAN/J1939/Diagnostics/Object Dictionary/PDO/I/O/CodesysConfiguration?)
    if sidebar_tab:
        # Sidebar tabs (left margin x<200) are UIA-visible
        from .field_change import click_left_tab
        if not click_left_tab(win, sidebar_tab):
            log(f"FAIL: sidebar tab '{sidebar_tab}'"); return result
        log(f"sidebar tab='{sidebar_tab}'")

    # 3. OCR-driven label click + value type
    if not change_numeric_field(label, value):
        log(f"FAIL: OCR could not find label '{label}'"); return result
    log(f"clicked + typed {value!r}")

    # 4. Save
    if save:
        common.save_project()
        log("saved")

    result["after_sha"] = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
    result["size_delta"] = PROJ.stat().st_size - len(open(PROJ,'rb').read())  # no, get from before_size
    # Recompute size_delta correctly
    bef_path_size = (backup_dir / f"backup_before_{label.replace('/','_').replace(' ','_')}_{value}.mtproject").stat().st_size if backup_dir else None
    if bef_path_size:
        result["size_delta"] = PROJ.stat().st_size - bef_path_size
    log(f"after sha={result['after_sha']} delta={result.get('size_delta')}")
    result["ok"] = result["before_sha"] != result["after_sha"]
    return result


def main():
    if len(sys.argv) < 4:
        print("Usage: python -m skills.e2e_explorer.recipes.ocr_field_change <device> <sidebar_tab|-> <label> <value>")
        sys.exit(1)
    tab = None if sys.argv[2] == "-" else sys.argv[2]
    bk = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\logs\e2e\recipes\ocr_field_change")
    r = run_field_change(sys.argv[1], tab, sys.argv[3], sys.argv[4], backup_dir=bk)
    print(f"\nRESULT ok={r['ok']} delta={r['size_delta']!s}")


if __name__ == "__main__":
    main()
