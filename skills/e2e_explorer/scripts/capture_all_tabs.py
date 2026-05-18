#!/usr/bin/env python3
"""Visit each sidebar tab in Configure panel + capture + OCR."""
import time, json
from pathlib import Path
from PIL import Image
from pywinauto import Application, mouse
import winocr
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "recipes"))
from common import connect, ensure_maximized

TABS = ["CAN", "J1939", "NMEA 2000", "Address Claiming", "Diagnostics",
        "Object Dictionary", "PDO", "I/O", "Events", "ISOBUS", "Library Manager"]

OUT = Path("logs/e2e/ui_capture/tabs")
OUT.mkdir(parents=True, exist_ok=True)


def click_sidebar_tab(win, tab_name: str) -> bool:
    """Click sidebar tab by Text label (left margin x<200)."""
    for t in win.descendants(control_type="Text"):
        try:
            r = t.rectangle()
            if r.left < 200 and t.window_text().strip() == tab_name:
                t.click_input()
                time.sleep(1.8)
                return True
        except Exception: pass
    return False


def ocr_image(img_path: Path) -> list[dict]:
    img = Image.open(img_path)
    r = winocr.recognize_pil_sync(img, lang="en-US")
    items = []
    for ln in r.get("lines", []):
        words = ln.get("words", [])
        if not words: continue
        xs = [w["bounding_rect"]["x"] for w in words]
        ys = [w["bounding_rect"]["y"] for w in words]
        xe = [w["bounding_rect"]["x"] + w["bounding_rect"]["width"] for w in words]
        items.append({"text": ln["text"].strip(), "x": int(min(xs)), "y": int(min(ys)),
                      "w": int(max(xe) - min(xs))})
    return items


def main():
    app, win = connect()
    ensure_maximized(win)
    time.sleep(0.5)
    summary = {}
    for tab in TABS:
        ok = click_sidebar_tab(win, tab)
        if not ok:
            print(f"  {tab}: FAIL to click")
            summary[tab] = {"clicked": False}
            continue
        # capture
        img_path = OUT / f"tab_{tab.replace('/','_').replace(' ','_')}.png"
        win.capture_as_image().save(str(img_path))
        # OCR
        items = ocr_image(img_path)
        # write per-tab OCR JSON
        (OUT / f"ocr_{tab.replace('/','_').replace(' ','_')}.json").write_text(
            json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {tab}: captured + {len(items)} OCR lines")
        summary[tab] = {"clicked": True, "ocr_lines": len(items), "screenshot": str(img_path)}

    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTotal tabs visited: {sum(1 for v in summary.values() if v.get('clicked'))}")


if __name__ == "__main__":
    main()
