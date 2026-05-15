#!/usr/bin/env python3
"""Phase 2 seeds: Diagnostics + IO + OD (RangeItem Min/Max, Pin Modes, OD entries)."""
import json
from pathlib import Path

SEQ_DIR = Path(__file__).parent.parent / "sequences"

# (idx, name, xpath_relative_to_device1, values, risk)
# Note: xpath uses Device[1] absolute prefix
SEEDS = [
    # Diagnostics RangeItems (Device 1)
    (45, "diag1_temp_min",         "Diagnostics/DiagnosticsItems/DiagnosticsRangeItem[1]/Minimum", ["-25", "-35", "-30"], "low"),
    (46, "diag1_temp_max",         "Diagnostics/DiagnosticsItems/DiagnosticsRangeItem[1]/Maximum", ["80", "90", "85"],     "low"),
    (47, "diag1_voltage_min",      "Diagnostics/DiagnosticsItems/DiagnosticsRangeItem[2]/Minimum", ["10", "8", "9"],       "low"),
    (48, "diag1_voltage_max",      "Diagnostics/DiagnosticsItems/DiagnosticsRangeItem[2]/Maximum", ["32", "35", "33"],     "low"),
    (49, "diag1_ref5v_min",        "Diagnostics/DiagnosticsItems/DiagnosticsRangeItem[3]/Minimum", ["4.6", "4.4", "4.5"],  "low"),
    (50, "diag1_ref5v_max",        "Diagnostics/DiagnosticsItems/DiagnosticsRangeItem[3]/Maximum", ["5.4", "5.6", "5.5"],  "low"),
    (51, "diag1_cycle_min",        "Diagnostics/DiagnosticsItems/DiagnosticsRangeItem[4]/Minimum", ["20", "15", "18"],     "low"),
    (52, "diag1_cycle_max",        "Diagnostics/DiagnosticsItems/DiagnosticsRangeItem[4]/Maximum", ["25", "35", "30"],     "low"),
    # IO Pin modes (Connector 1)
    (53, "io_pin2_mode",           "IO/Connectors/Connector[1]/Pins/Pin[1]/SelectedModes", ["3", "4", "5"], "medium"),
    (54, "io_pin3_mode",           "IO/Connectors/Connector[1]/Pins/Pin[2]/SelectedModes", ["3", "5", "4"], "medium"),
    (55, "io_pin7_mode",           "IO/Connectors/Connector[1]/Pins/Pin[3]/SelectedModes", ["4", "5", "3"], "medium"),
    # OD entries (CAN Parameters / ObjectDictionary)
    (56, "od1_use_checksum",       "CANs/CAN/Parameters/ObjectDictionary/ObjectDictionaryIndex[1]/UseChecksum", ["true", "false"], "low"),
    (57, "od1_description",        "CANs/CAN/Parameters/ObjectDictionary/ObjectDictionaryIndex[1]/Description", ["test_desc", ""], "low"),
    (58, "od_2000_data_type",      "CANs/CAN/Parameters/ObjectDictionary/ObjectDictionaryIndex[8]/DataType", ["WORD", "INT", "DWORD"], "medium"),
]

written = 0
for idx, name, rel, values, risk in SEEDS:
    seed = {
        "name": name,
        "goal": f"Device[1] {rel.replace('/', '.')} 변경 시 XML 변화 관찰",
        "xpath": f"/MtProject/Device[1]/{rel}",
        "values": values,
        "restore_on_finish": True,
        "expected_node_path": f"Device[1]/{rel}",
        "risk": risk,
    }
    fn = SEQ_DIR / f"{idx:02d}_{name}.json"
    fn.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    written += 1

print(f"Generated {written} phase-2 seeds in {SEQ_DIR}")
print(f"Total seeds: {len(list(SEQ_DIR.glob('*.json')))}")
