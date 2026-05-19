"""디바이스 템플릿(XML)에서 핀별 지원 모드 추출.

권위 소스: C:\\Program Files (x86)\\Epec\\MultiTool Creator 8.4\\Resources\\Config\\Devices\\<model>.xml

용도:
  - io_pin 시드 모드 값 검증 (잘못된 mode 값 사전 차단)
  - F_io.json 자동 생성 (`generate_io_seeds.py`)
  - 야간 사이클 시드 설계 시 핀당 valid mode 자동 채움
"""
import xml.etree.ElementTree as ET
from pathlib import Path

DEVICES_DIR = Path(r"C:\Program Files (x86)\Epec\MultiTool Creator 8.4\Resources\Config\Devices")

# XML #lang.IO.Mode.Xxx# → UI button label
UI_LABEL = {
    "Di": "DI", "Do": "DO", "Pwm": "PWM", "Ai": "AI",
    "Gnd": "GND", "Supply": "Supply", "FiveVoltRef": "5V Ref",
    "StepMotor": "Step Motor", "Fb": "FB", "AiRatiometric": "AI Ratio",
    "Can1L": "CAN1L", "Can1H": "CAN1H", "Can1LT": "CAN1LT",
    "Can2L": "CAN2L", "Can2H": "CAN2H",
    "PulseInput1ChPulseWidth": "PI1 PW",
    "PulseInput1ChPulseCount": "PI1 PC",
    "PulseInput1ChFrequency": "PI1 Freq",
    "PulseInput1ChPlusResetChn": "PI1+Rst",
    "PulseInput2ChPulseCount": "PI2 PC",
    "PulseInput2ChPlusResetChn": "PI2+Rst",
    "PulseInput1ChWidthPlusCount": "PI1 W+C",
    "PulseInput1ChFrequencyPlusCount": "PI1 F+C",
    "NotUsed": "Not Used", "Always": "Always", "NullObject": "—",
    "Reserved": "Reserved",
}


def load_device(model: str) -> dict:
    """3606_21 같은 model 이름 → {mode_table, pins}."""
    xml_path = DEVICES_DIR / f"{model}.xml"
    if not xml_path.exists():
        raise FileNotFoundError(f"device template not found: {xml_path}")
    root = ET.parse(xml_path).getroot()

    modes = {}
    for io in root.iter("IO"):
        ms = io.find("Modes")
        if ms is None: continue
        for m in ms.findall("Mode"):
            mid = m.findtext("Id"); nm = m.findtext("Name") or ""
            if not mid or not mid.lstrip("-").isdigit(): continue
            short = nm.split(".")[-1].rstrip("#").strip() if nm.startswith("#lang.") else nm
            modes[int(mid)] = short
        break

    pins = {}
    for pin in root.iter("Pin"):
        pid = pin.findtext("Id"); vname = pin.findtext("Variable") or ""
        if not pid or not pid.isdigit(): continue
        sup = set()
        for tc in pin.iter("TagCode"):
            sm = tc.get("SupportedModes")
            if sm:
                for x in sm.split(","):
                    x = x.strip()
                    if x.lstrip("-").isdigit(): sup.add(int(x))
        default = pin.findtext("DefaultMode")
        pins[int(pid)] = {
            "variable": vname,
            "supported_mode_ids": sorted(sup),
            "supported_mode_names": [modes.get(s, f"?{s}") for s in sorted(sup)],
            "ui_labels": [UI_LABEL.get(modes.get(s, ""), modes.get(s, str(s))) for s in sorted(sup)],
            "default_mode_id": int(default) if default and default.lstrip("-").isdigit() else None,
        }
    return {"model": model, "mode_table": modes, "pins": pins}


def pick_mode_for_pin(device: dict, pin_id: int, preferred: list[str] = None) -> str:
    """핀 지원 모드 중 preferred 순서로 첫 매칭 UI label 반환. 없으면 첫 번째 지원 모드."""
    if pin_id not in device["pins"]: return None
    labels = device["pins"][pin_id]["ui_labels"]
    if preferred:
        for p in preferred:
            if p in labels: return p
    return labels[0] if labels else None


if __name__ == "__main__":
    import sys, json
    model = sys.argv[1] if len(sys.argv) > 1 else "3606_21"
    d = load_device(model)
    print(f"Device {model}: {len(d['mode_table'])} modes, {len(d['pins'])} pins")
    for pid, info in sorted(d["pins"].items())[:12]:
        print(f"  Pin {pid:>3} ({info['variable']:8s}) default={info['default_mode_id']} ui_labels={info['ui_labels']}")
