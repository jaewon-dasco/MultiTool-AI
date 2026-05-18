#!/usr/bin/env python3
"""Batch OCR all screenshots in logs/e2e/ui_capture/ + match against seed xpaths."""
import json, re
from pathlib import Path
from collections import defaultdict
import winocr
from PIL import Image

SCR_DIR = Path("logs/e2e/ui_capture")
SEEDS_DIR = Path("skills/e2e_explorer/sequences")
OUT_DIR = Path("logs/e2e/ocr_analysis")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def ocr_one(img_path: Path) -> list[dict]:
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
                      "w": int(max(xe) - min(xs)), "h": int(words[0]["bounding_rect"]["height"])})
    return items


def xpath_field_name(xpath: str) -> str:
    """Extract the last field name from xpath (e.g. CodesysNodeId)."""
    return xpath.rsplit("/", 1)[-1].split("[")[0]


def camel_to_label(name: str) -> str:
    """CodesysNodeId → 'Codesys Node Id' (rough UI label guess).
    Also keeps NodeID-style abbreviations."""
    # Insert space before each uppercase that is preceded by lowercase
    s = re.sub(r"(?<=[a-z])([A-Z])", r" \1", name)
    # Common substitutions
    s = s.replace("Node Id", "Node-ID").replace("Node id", "Node-ID")
    s = s.replace("Cob Id", "COB-ID").replace("Cob ID", "COB-ID")
    s = s.replace("C R C", "CRC").replace("Cr c", "CRC")
    s = s.replace("E D S", "EDS").replace("Eds", "EDS")
    s = s.replace("E M C Y", "EMCY").replace("Emcy", "EMCY")
    s = s.replace("S D O", "SDO").replace("Sdo", "SDO")
    s = s.replace("Pd Os", "PDOs").replace("Pdo", "PDO")
    s = s.replace("Dm 1", "DM1").replace("Dm 2", "DM2")
    s = s.replace("D T Cs", "DTCs").replace("Dtcs", "DTCs")
    s = s.replace("Nmt", "NMT").replace("Iso bus", "ISOBUS")
    return s.strip()


def fuzzy_match(label_target: str, ocr_text: str) -> float:
    """Return similarity 0..1. Strict tokens but tolerant to single-char OCR errors."""
    t = label_target.lower()
    o = ocr_text.lower()
    if t == o: return 1.0
    # token overlap
    t_tokens = set(re.findall(r"\w+", t))
    o_tokens = set(re.findall(r"\w+", o))
    if not t_tokens: return 0.0
    overlap = t_tokens & o_tokens
    return len(overlap) / len(t_tokens)


def main():
    # 1) OCR all screenshots
    all_ocr = {}
    pngs = sorted(SCR_DIR.glob("*.png"))
    print(f"OCR {len(pngs)} screenshots...")
    for p in pngs:
        try:
            items = ocr_one(p)
            all_ocr[p.name] = items
            print(f"  {p.name}: {len(items)} lines")
        except Exception as e:
            print(f"  {p.name}: ERR {e}")
            all_ocr[p.name] = []
    (OUT_DIR / "all_ocr.json").write_text(json.dumps(all_ocr, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2) Load seeds
    seeds = []
    for fp in sorted(SEEDS_DIR.glob("*.json")):
        s = json.load(open(fp, encoding="utf-8"))
        s["_idx"] = int(fp.stem.split("_")[0])
        seeds.append(s)
    print(f"\nLoaded {len(seeds)} seeds")

    # 3) Match each seed field against any OCR text across screenshots
    matches = []
    for s in seeds:
        field = xpath_field_name(s["xpath"])
        label_guess = camel_to_label(field)
        best = {"score": 0, "ocr_text": "", "screenshot": "", "x": 0, "y": 0}
        for scr_name, items in all_ocr.items():
            for it in items:
                sc = fuzzy_match(label_guess, it["text"])
                if sc > best["score"]:
                    best = {"score": sc, "ocr_text": it["text"], "screenshot": scr_name, "x": it["x"], "y": it["y"]}
        matches.append({
            "idx": s["_idx"], "name": s["name"], "xpath": s["xpath"],
            "field": field, "label_guess": label_guess, "best": best,
            "values": s["values"],
        })

    (OUT_DIR / "seed_label_matches.json").write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4) Report — by match quality
    fully = [m for m in matches if m["best"]["score"] >= 1.0]
    partial = [m for m in matches if 0.5 <= m["best"]["score"] < 1.0]
    weak = [m for m in matches if 0.0 < m["best"]["score"] < 0.5]
    miss = [m for m in matches if m["best"]["score"] == 0]

    print(f"\n=== Match summary ({len(matches)} seeds) ===")
    print(f"  FULL  (score=1.0): {len(fully)}")
    print(f"  PARTIAL (0.5..1.0): {len(partial)}")
    print(f"  WEAK    (0..0.5)  : {len(weak)}")
    print(f"  MISS    (0)       : {len(miss)}")

    for tag, lst in [("FULL", fully), ("PARTIAL", partial), ("WEAK", weak), ("MISS", miss)]:
        print(f"\n--- {tag} ({len(lst)}) ---")
        for m in lst[:30]:
            ocr_info = f"'{m['best']['ocr_text']}' in {m['best']['screenshot']}" if m['best']['score'] > 0 else "—"
            print(f"  [{m['idx']:02d}] {m['label_guess']:40} ↔ {ocr_info}")


if __name__ == "__main__":
    main()
