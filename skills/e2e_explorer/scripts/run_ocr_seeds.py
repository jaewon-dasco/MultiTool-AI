#!/usr/bin/env python3
"""Execute selected OCR-matched seeds via UI: change → save → XML diff → restore."""
import json, time, hashlib, shutil, difflib
from pathlib import Path
from PIL import ImageGrab, Image
import winocr
from pywinauto import Application, mouse
from pywinauto.keyboard import send_keys
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "recipes"))
from common import connect, ensure_maximized, save_project

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")
ORIG_BAK = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject.bak.ui_exp_20260515_103230")
OUT_DIR = Path("logs/e2e/ocr_runs")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def screenshot_ocr():
    img = ImageGrab.grab()
    r = winocr.recognize_pil_sync(img, lang="en-US")
    out = []
    for ln in r.get("lines", []):
        words = ln.get("words", [])
        if not words: continue
        xs = [w["bounding_rect"]["x"] for w in words]
        ys = [w["bounding_rect"]["y"] for w in words]
        xe = [w["bounding_rect"]["x"] + w["bounding_rect"]["width"] for w in words]
        ye = [w["bounding_rect"]["y"] + w["bounding_rect"]["height"] for w in words]
        out.append({"text": ln["text"].strip(), "x": int(min(xs)), "y": int(min(ys)),
                    "right": int(max(xe)), "bottom": int(max(ye)),
                    "yc": int((min(ys)+max(ye))//2)})
    return out


def find_label(ocr_items, label_target: str):
    """Exact then fuzzy match. Return first match (smallest x for stability)."""
    t = label_target.lower()
    exact = [i for i in ocr_items if i["text"].lower() == t]
    if exact:
        exact.sort(key=lambda i: (i["y"], i["x"]))
        return exact[0]
    # contains
    contained = [i for i in ocr_items if t in i["text"].lower()]
    if contained:
        contained.sort(key=lambda i: len(i["text"]))  # prefer shortest
        return contained[0]
    return None


def change_numeric_at_label(label_target: str, value: str, offset_x: int = 100) -> bool:
    ocr = screenshot_ocr()
    item = find_label(ocr, label_target)
    if not item: return False
    click_x = item["right"] + offset_x
    click_y = item["yc"]
    mouse.click(coords=(click_x, click_y))
    time.sleep(0.3)
    send_keys("^a"); time.sleep(0.1)
    send_keys("{DELETE}"); time.sleep(0.1)
    send_keys(value); time.sleep(0.2)
    send_keys("{TAB}"); time.sleep(0.4)
    return True


def restore_original():
    shutil.copy(ORIG_BAK, PROJ)


def xml_summary_diff(before_path: Path, after_path: Path):
    b = before_path.read_text(encoding="utf-8", errors="replace").splitlines()
    a = after_path.read_text(encoding="utf-8", errors="replace").splitlines()
    diff = list(difflib.unified_diff(b, a, n=0, lineterm=""))
    removed = [ln[1:] for ln in diff if ln.startswith("-") and not ln.startswith("---")]
    added = [ln[1:] for ln in diff if ln.startswith("+") and not ln.startswith("+++")]
    # Value changes by tag
    import re
    changes = []
    for r_ln in removed:
        m = re.search(r"<(\w+)>([^<>]+)</\1>", r_ln)
        if not m: continue
        for a_ln in added:
            m2 = re.search(r"<(\w+)>([^<>]+)</\1>", a_ln)
            if m2 and m.group(1) == m2.group(1) and m.group(2) != m2.group(2):
                changes.append((m.group(1), m.group(2), m2.group(2)))
                break
    return {"raw_added": len(added), "raw_removed": len(removed),
            "value_changes": changes[:30]}


# Seeds to run (FULL match, single-label)
TARGETS = [
    {"idx": 6,  "label": "Codesys Node-ID",         "value": "5"},
    {"idx": 7,  "label": "Node-ID Offset for PDOs", "value": "64"},
    {"idx": 27, "label": "Device Profile",          "value": "402"},
]


def main():
    print("=== OCR-driven UI seed execution ===")
    results = []
    for t in TARGETS:
        # Restore baseline before each test
        restore_original()
        time.sleep(0.5)
        before_sha = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
        before_size = PROJ.stat().st_size
        print(f"\n[seed {t['idx']:02d}] {t['label']} -> {t['value']}")
        print(f"  before sha={before_sha} size={before_size}")
        # Backup before-snapshot
        bef_copy = OUT_DIR / f"seed{t['idx']:02d}_before.mtproject"
        shutil.copy(PROJ, bef_copy)

        ok = change_numeric_at_label(t["label"], t["value"])
        if not ok:
            print(f"  FAIL: label '{t['label']}' not found on screen")
            results.append({**t, "ok": False, "reason": "label not found"})
            continue
        print(f"  clicked + typed {t['value']!r}")
        save_project()

        after_sha = hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]
        after_size = PROJ.stat().st_size
        print(f"  after sha={after_sha} size={after_size} delta={after_size-before_size:+d}")
        aft_copy = OUT_DIR / f"seed{t['idx']:02d}_after.mtproject"
        shutil.copy(PROJ, aft_copy)
        summary = xml_summary_diff(bef_copy, aft_copy)
        print(f"  diff: -{summary['raw_removed']} +{summary['raw_added']} lines")
        if summary["value_changes"]:
            print(f"  value changes:")
            for tag, old, new in summary["value_changes"][:10]:
                print(f"    <{tag}>: {old} -> {new}")
        results.append({**t, "ok": True, "before_sha": before_sha, "after_sha": after_sha,
                        "size_delta": after_size-before_size, "diff_summary": summary})

    (OUT_DIR / "run_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    # Final restore
    restore_original()
    print(f"\nDone. Final sha={hashlib.sha256(PROJ.read_bytes()).hexdigest()[:16]} (restored)")


if __name__ == "__main__":
    main()
