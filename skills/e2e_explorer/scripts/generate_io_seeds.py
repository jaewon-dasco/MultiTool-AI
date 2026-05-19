#!/usr/bin/env python3
"""디바이스 템플릿에서 핀별 지원 모드를 읽어 F_io.json 자동 생성.

사용:
  py scripts/generate_io_seeds.py [model=3606_21] [pins=2,3,7,8,9,10,11,12]
"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes.device_modes import load_device, pick_mode_for_pin

OUT = ROOT / "skills" / "e2e_explorer" / "sequences_ui" / "F_io.json"


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else "3606_21"
    pin_arg = sys.argv[2] if len(sys.argv) > 2 else "2,3,7,8,9,10,11,12"
    pin_ids = [int(x) for x in pin_arg.split(",")]
    connector = 1

    d = load_device(model)
    # 각 핀마다 선호 모드 순환 (DI/DO/PWM)
    rotation = ["DI", "DO", "PWM"]
    seeds = []
    for i, pid in enumerate(pin_ids):
        info = d["pins"].get(pid)
        if not info:
            print(f"WARN: pin {pid} not in device {model}"); continue
        preferred = [rotation[i % len(rotation)]] + rotation
        chosen = pick_mode_for_pin(d, pid, preferred)
        if chosen is None:
            print(f"WARN: pin {pid} has no UI labels"); continue
        seeds.append({
            "idx": 50 + i,
            "name": f"io_pin{connector}_{pid}_mode",
            "label": f"{connector}.{pid}",
            "value": chosen,
            "tab": "I/O",
            "expected_kind": "io_mode_button",
            "connector": str(connector),
            "note": f"{info['variable']} → mode {chosen} (지원: {info['ui_labels']})"
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(seeds, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(seeds)} seeds → {OUT}")
    for s in seeds:
        print(f"  idx={s['idx']:2d} pin={s['label']:5s} value={s['value']}  ({s['note']})")


if __name__ == "__main__":
    main()
