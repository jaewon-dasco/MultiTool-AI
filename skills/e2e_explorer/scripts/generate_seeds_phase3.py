#!/usr/bin/env python3
"""Phase 3 seeds: CodesysConfiguration + PDO + Pin Variable names."""
import json
from pathlib import Path

SEQ_DIR = Path(__file__).parent.parent / "sequences"

SEEDS = [
    # CodesysConfiguration
    (59, "cds_max_cob_ids",        "CodesysConfiguration/MaxNumberOfCobIds",            ["200", "50", "100"], "low"),
    (60, "cds_max_request_cb",     "CodesysConfiguration/MaxNumberOfRequestCallbacks",  ["20", "5", "10"],     "low"),
    (61, "cds_saved_param_cycle",  "CodesysConfiguration/SavedParameterCountPerCycle",  ["100", "25", "50"],   "low"),
    # PDO mappings (RPDO)
    (62, "rpdo1_cob_id",           "ProcessDataObjectMappings/Device[1]/CANs/CAN/ReceiveProcessDataObject[1]/CobId", ["386", "384", "385"], "medium"),
    (63, "rpdo1_dlc",              "ProcessDataObjectMappings/Device[1]/CANs/CAN/ReceiveProcessDataObject[1]/DataLengthCode", ["1", "8", "0"], "medium"),
    # Pin Variable names (string, very safe)
    (64, "pin1_variable_name",     "IO/Connectors/Connector[1]/Pins/Pin[1]/Variable", ["TEST_PIN1", "VAVLE_UP"], "low"),
    (65, "pin2_variable_name",     "IO/Connectors/Connector[1]/Pins/Pin[2]/Variable", ["TEST_PIN2", "VAVLE_DN"], "low"),
]

written = 0
for idx, name, rel, values, risk in SEEDS:
    # PDO xpath uses MachineType path, not Device[1] directly
    if rel.startswith("ProcessDataObjectMappings"):
        xpath = f"/MtProject/Project/MachineType/{rel}"
    else:
        xpath = f"/MtProject/Device[1]/{rel}"
    seed = {
        "name": name,
        "goal": f"{xpath} 변경 시 XML 변화 관찰",
        "xpath": xpath,
        "values": values,
        "restore_on_finish": True,
        "expected_node_path": rel,
        "risk": risk,
    }
    fn = SEQ_DIR / f"{idx:02d}_{name}.json"
    fn.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    written += 1

print(f"Generated {written} phase-3 seeds")
print(f"Total seeds: {len(list(SEQ_DIR.glob('*.json')))}")
