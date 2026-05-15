#!/usr/bin/env python3
"""Generate seed sequence JSONs from a definition table.

Covers full CAN Settings + J1939 + RPDO/TPDO basics so the night cycle
can run all features sequentially before repeating for determinism.
"""
import json
from pathlib import Path

SEQ_DIR = Path(__file__).parent.parent / "sequences"
SEQ_DIR.mkdir(parents=True, exist_ok=True)

# (filename_index, name, xpath_relative, values_cycle, risk)
# xpath_relative is appended to /MtProject/Device[1]/CANs/CAN
SEEDS = [
    # CAN Settings (Numeric)
    (11, "can1_sync_counter_max",      "Settings/SyncCounterMax",          ["120", "240", "200", "240"], "low"),
    (12, "can1_sync_cob_id",           "Settings/SyncCobID",               ["256", "384", "128"],          "low"),
    (13, "can1_delay_before_config",   "Settings/DelayBeforeConfiguration",["500", "2000", "1000"],        "low"),
    (14, "can1_config_start_timeout",  "Settings/ConfigurationStartTimeout",["5", "20", "10"],             "low"),
    (15, "can1_sdo_query_interval",    "Settings/SdoQueryInterval",        ["100", "500", "0"],            "low"),
    (16, "can1_eds_product_number",    "Settings/EDSProductNumber",        ["1234", "5678", "0"],          "low"),
    (17, "can1_eds_vendor_id",         "Settings/EDSVendorId",             ["100", "200", "0"],            "low"),
    (18, "can1_save_index",            "Settings/SaveIndex",               ["4113", "4096", "4112"],       "low"),
    (19, "can1_save_sub_index",        "Settings/SaveSubIndex",            ["2", "3", "1"],                "low"),
    (20, "can1_save_timeout",          "Settings/SaveTimeout",             ["500", "2000", "1000"],        "low"),
    (21, "can1_crc_index",             "Settings/CRCIndex",                ["8274", "8275", "8273"],       "low"),
    (22, "can1_crc_sub_index",         "Settings/CRCSubIndex",             ["1", "3", "2"],                "low"),
    (23, "can1_crc_valid_index",       "Settings/CRCValidIndex",           ["8274", "8276", "8273"],       "low"),
    (24, "can1_crc_valid_sub_index",   "Settings/CRCValidSubIndex",        ["2", "3", "1"],                "low"),
    (25, "can1_crc_valid_value",       "Settings/CRCValidValue",           ["2", "0", "1"],                "low"),
    (26, "can1_crc_valid_delay",       "Settings/CRCValidDelay",           ["500", "2000", "1000"],        "low"),
    (27, "can1_device_profile",        "Settings/DeviceProfile",           ["401", "402", "405"],          "medium"),
    # CAN Settings (Boolean / Enum)
    (28, "can1_message_type",          "Settings/MessageType",             ["Extended", "Short"],          "low"),
    (29, "can1_take_node_id_from_comm","Settings/TakeNodeIdFromCommParams",["true", "false"],              "low"),
    (30, "can1_create_csdo",           "Settings/CreateCsdoInstances",     ["true", "false"],              "low"),
    (31, "can1_sync_producer",         "Settings/SyncProducer",            ["True", "False"],              "low"),
    (32, "can1_sync_counter",          "Settings/SyncCounter",             ["True", "False"],              "low"),
    (33, "can1_emcy_producer",         "Settings/EMCYProducer",            ["True", "False"],              "low"),
    (34, "can1_emcy_consumer",         "Settings/EMCYConsumer",            ["True", "False"],              "low"),
    (35, "can1_sdo_query_enable",      "Settings/SdoQueryEnable",          ["true", "false"],              "low"),
    (36, "can1_no_configuration",      "Settings/NoConfiguration",         ["true", "false"],              "low"),
    (37, "can1_save_configuration",    "Settings/SaveConfiguration",       ["true", "false"],              "low"),
    (38, "can1_verify_method",         "Settings/VerifyMethod",            ["None", "Compare", "CRC"],     "low"),
    (39, "can1_use_crc_validity",      "Settings/UseCRCValidityIndex",     ["true", "false"],              "low"),
    # J1939
    (40, "can1_j1939_dm1_producer",    "J1939/DM1Producer",                ["true", "false"],              "low"),
    (41, "can1_j1939_dm2_producer",    "J1939/DM2Producer",                ["true", "false"],              "low"),
    (42, "can1_j1939_dm2_saving",      "J1939/DM2SavingToNonVolatileMemory",["true", "false"],             "low"),
    (43, "can1_j1939_num_dtcs",        "J1939/NumberOfDTCs",               ["1", "4", "2"],                "low"),
    (44, "can1_j1939_manual_address",  "J1939/ManualAddress",              ["10", "100", "0"],             "low"),
]

written = 0
for idx, name, rel, values, risk in SEEDS:
    seed = {
        "name": name,
        "goal": f"Device[1] CAN1 {rel.replace('/', '.')} 변경 시 XML 변화 관찰",
        "xpath": f"/MtProject/Device[1]/CANs/CAN/{rel}",
        "values": values,
        "restore_on_finish": True,
        "expected_node_path": f"Device[1]/CANs/CAN/{rel}",
        "risk": risk,
    }
    fn = SEQ_DIR / f"{idx:02d}_{name}.json"
    fn.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    written += 1

print(f"Generated {written} seed sequences in {SEQ_DIR}")
print(f"Total seeds now: {len(list(SEQ_DIR.glob('*.json')))}")
