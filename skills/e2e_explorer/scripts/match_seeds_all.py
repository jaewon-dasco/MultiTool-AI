#!/usr/bin/env python3
"""Match 60 seeds against OCR results from all tab captures (tabs + existing screenshots)."""
import json, re
from pathlib import Path
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SEEDS_DIR = Path("skills/e2e_explorer/sequences")
TABS_DIR = Path("logs/e2e/ui_capture/tabs")
SCR_DIR = Path("logs/e2e/ui_capture")
OUT_DIR = Path("logs/e2e/ocr_analysis")


def camel_to_label(name: str) -> str:
    s = re.sub(r"(?<=[a-z])([A-Z])", r" \1", name)
    s = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r" \1", s)
    for old, new in [("Node Id","Node-ID"),("Node id","Node-ID"),("Cob Id","COB-ID"),
                     ("Cob ID","COB-ID"),("C R C","CRC"),("Cr c","CRC"),
                     ("E D S","EDS"),("Eds","EDS"),("E M C Y","EMCY"),("Emcy","EMCY"),
                     ("S D O","SDO"),("Sdo","SDO"),("Pd Os","PDOs"),("Pdo","PDO"),
                     ("Dm 1","DM1"),("Dm 2","DM2"),("D T Cs","DTCs"),("Dtcs","DTCs"),
                     ("Nmt","NMT"),("Iso bus","ISOBUS"),("J 1939","J1939"),("J1 939","J1939")]:
        s = s.replace(old, new)
    return s.strip()


def fuzzy(target: str, text: str) -> float:
    t = target.lower(); o = text.lower()
    if t == o: return 1.0
    if t in o: return 0.95
    t_tokens = set(re.findall(r"\w+", t))
    o_tokens = set(re.findall(r"\w+", o))
    if not t_tokens: return 0.0
    return len(t_tokens & o_tokens) / len(t_tokens)


# Load all OCR sources
all_ocr = {}  # source -> [items]
for fp in TABS_DIR.glob("ocr_*.json"):
    tab = fp.stem.replace("ocr_", "")
    all_ocr[f"tab:{tab}"] = json.loads(fp.read_text(encoding="utf-8"))
# Also include existing
existing_path = OUT_DIR / "all_ocr.json"
if existing_path.exists():
    for name, items in json.loads(existing_path.read_text(encoding="utf-8")).items():
        all_ocr[f"scr:{name}"] = items

print(f"OCR sources: {len(all_ocr)}")

# Load seeds
seeds = []
for fp in sorted(SEEDS_DIR.glob("*.json")):
    s = json.load(open(fp, encoding="utf-8"))
    s["_idx"] = int(fp.stem.split("_")[0])
    seeds.append(s)

# Match each seed
matches = []
for s in seeds:
    field = s["xpath"].rsplit("/", 1)[-1].split("[")[0]
    label = camel_to_label(field)
    best = {"score": 0, "text": "", "source": "", "x": 0, "y": 0}
    for src, items in all_ocr.items():
        for it in items:
            sc = fuzzy(label, it["text"])
            if sc > best["score"]:
                best = {"score": sc, "text": it["text"], "source": src, "x": it["x"], "y": it["y"]}
    matches.append({"idx": s["_idx"], "name": s["name"], "xpath": s["xpath"],
                    "field": field, "label_guess": label, "best": best})

OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "seed_matches_v2.json").write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")

# Report
fully = [m for m in matches if m["best"]["score"] >= 0.95]
partial = [m for m in matches if 0.5 <= m["best"]["score"] < 0.95]
weak = [m for m in matches if 0.0 < m["best"]["score"] < 0.5]
miss = [m for m in matches if m["best"]["score"] == 0]

print(f"\n=== Match (60 seeds total — 5 verified already skipped at runtime) ===")
print(f"  FULL  ≥0.95:  {len(fully)}")
print(f"  PARTIAL:      {len(partial)}")
print(f"  WEAK:         {len(weak)}")
print(f"  MISS:         {len(miss)}")

for tag, lst in [("FULL", fully), ("PARTIAL", partial), ("WEAK", weak), ("MISS", miss)]:
    print(f"\n--- {tag} ({len(lst)}) ---")
    for m in lst:
        b = m["best"]
        info = f"'{b['text'][:40]}' @ {b['source']}" if b['score'] > 0 else "—"
        print(f"  [{m['idx']:02d}] {m['label_guess']:40} ↔ {b['score']:.2f}  {info}")
