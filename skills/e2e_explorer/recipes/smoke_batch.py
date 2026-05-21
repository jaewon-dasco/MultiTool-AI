"""Phase 1 smoke batch — verified 시드들을 한 세션에 일괄 적용.

흐름:
1. restore baseline + MultiTool 재시작 (한 번)
2. for seed in verified_seeds: apply UI change only (no save/export per seed)
3. 한 번 Save (Ctrl+S)
4. 한 번 Export (Ctrl+Alt+E)
5. MultiTool 종료 (정상)
6. baseline 복원

목적: regression test — 이전 cycle에서 verified된 시드들이 여전히 작동하는지 빠르게 확인.
ML signal은 추출하지 않음 (이미 isolated cycle에서 수집됨).

판정:
- 모든 시드 UI 적용 OK + Save OK + Export OK → batch_ok=True (verified 유지)
- 한 시드라도 UI 적용 실패 → 해당 시드 demote, batch_ok=False
- Save/Export 실패 → 전체 batch demote (격리 못함)
"""
import json, shutil, time, traceback
from pathlib import Path
from . import common, ocr_helpers
from .seed_runner_ui import (
    RUN_ROOT, PROJ, ORIG_BAK, restore_baseline, restart_multitool_clean, sha
)


def _apply_one_seed_ui_only(win, seed: dict, current_tab_ref: list) -> dict:
    """UI 적용만 수행. save/export/baseline_restore 없음.

    current_tab_ref: [str|None] — list로 감싸 mutable 참조. 탭 전환 최소화.
    Returns: {name, ok, action, kind, error?}
    """
    from pywinauto.keyboard import send_keys
    name = seed.get("name", "?")
    label = seed["label"]
    value = seed["value"]
    sidebar_tab = seed.get("tab")
    r = {"name": name, "idx": seed.get("idx"), "ok": False, "action": None, "kind": None}

    try:
        # Tab 전환 (이전 시드와 다른 경우만)
        if sidebar_tab and sidebar_tab != current_tab_ref[0]:
            from .field_change import click_left_tab, open_configure_panel
            if not open_configure_panel(win, "CU_3606_21_1"):
                r["error"] = "configure_panel_failed"; return r
            time.sleep(0.5)
            if not click_left_tab(win, sidebar_tab):
                r["error"] = f"tab_switch_failed '{sidebar_tab}'"; return r
            current_tab_ref[0] = sidebar_tab

        # UI 적용 — seed_runner_ui.run_one_seed의 action 분기와 동일 로직.
        # 단순화 위해 expected_kind 단일 시드만 처리.
        expected_kind = seed.get("expected_kind")
        if expected_kind == "toolbar_action":
            ok = ocr_helpers.click_toolbar_button(win, label)
            action = {"ok": ok, "kind": "toolbar_action", "action": f"toolbar.click '{label}'"}
        elif expected_kind == "toolbar_action_with_dialog":
            if seed.get("dialog") and label in ("Add Device", "Add Slave Device"):
                from .add_device_recipe import add_device_via_dropdown
                dlg = seed["dialog"]
                action = add_device_via_dropdown(
                    win, model=dlg.get("model", ""), cds=dlg.get("cds", "2.3"),
                    family=dlg.get("family"), slave=(label == "Add Slave Device"))
            else:
                ok = ocr_helpers.click_toolbar_button(win, label)
                action = {"ok": ok, "kind": "toolbar_action_with_dialog",
                          "action": f"toolbar.click '{label}' + dialog"}
        elif expected_kind == "shortcut":
            send_keys(seed.get("shortcut", "")); time.sleep(1)
            action = {"ok": True, "kind": "shortcut", "action": f"sent '{seed['shortcut']}'"}
        elif expected_kind == "io_mode_button":
            from .io_pin_recipe import set_pin_mode
            action = set_pin_mode(win, pin_id=label, mode_short=value,
                                   connector=seed.get("connector", "1"))
        elif expected_kind == "io_variable_name":
            from .io_pin_recipe import set_pin_variable_name
            action = set_pin_variable_name(win, pin_id=label, new_name=value,
                                            connector=seed.get("connector", "1"))
        elif expected_kind == "diagnostics_minmax":
            from .diagnostics_recipe import set_alarm_limit
            action = set_alarm_limit(win, label_keyword=label,
                                     which=seed.get("which", "Max"), value=value)
        elif expected_kind == "network_property":
            from .network_property import set_network_property
            action = set_network_property(win, network=seed.get("target_network", "NETWORK1"),
                                          field_label=label, value=value)
        elif expected_kind == "device_panel_x_button":
            from .device_disconnect import device_disconnect_from_network
            target = seed.get("target", "CU_3606_21_1")
            rr = device_disconnect_from_network("NETWORK1", target, save=False)
            action = {"ok": rr["ok"], "kind": "device_panel_x_button",
                      "action": f"disconnect {target}"}
        elif expected_kind == "od_toolbar":
            from .od_recipe import execute_od_action
            action = execute_od_action(win, seed.get("action_name", "add_index"))
        elif expected_kind == "pdo_toolbar":
            from .pdo_recipe import pdo_add, pdo_remove_or_select_and_remove
            d = seed.get("direction", "Tx"); op = seed.get("operation", "Add")
            action = pdo_add(win, d) if op == "Add" else pdo_remove_or_select_and_remove(win, d)
        else:
            action = ocr_helpers.set_field_auto(label, value, expected_kind=expected_kind,
                                                 table_column=seed.get("table_column"))

        r["kind"] = action.get("kind")
        r["action"] = action.get("action")
        r["ok"] = bool(action.get("ok"))
        return r
    except Exception as e:
        r["error"] = f"exception: {e}"
        r["traceback"] = traceback.format_exc()
        return r


def run_smoke_batch(verified_seeds: list) -> dict:
    """verified_seeds를 한 세션에 일괄 적용.

    Returns:
      {batch_ok: bool, applied_results: [...], save_ok, export_ok,
       failed_seed_names: [str], duration: float}
    """
    t0 = time.time()
    out = {"batch_ok": False, "applied_results": [], "save_ok": False,
           "export_ok": False, "failed_seed_names": [], "duration": 0.0,
           "n_seeds": len(verified_seeds)}

    if not verified_seeds:
        out["batch_ok"] = True; out["duration"] = time.time() - t0
        return out

    print(f"  [smoke_batch] {len(verified_seeds)} verified seeds — one session")

    try:
        restore_baseline()
        time.sleep(0.3)
        if not restart_multitool_clean():
            out["error"] = "multitool_restart_failed"; return out

        app, win = common.connect()
        common.ensure_maximized(win)
        current_tab = [None]  # mutable ref

        for s in verified_seeds:
            ar = _apply_one_seed_ui_only(win, s, current_tab)
            out["applied_results"].append(ar)
            if not ar["ok"]:
                out["failed_seed_names"].append(ar["name"])
                print(f"    FAIL: {ar['name']} — {ar.get('error') or ar.get('action')}")
            time.sleep(0.3)  # 시드 간 UI 안정

        # 한 번 Save
        try:
            common.save_project()
            time.sleep(1.0)
            out["save_ok"] = True
        except Exception as e:
            out["save_error"] = str(e)

        # 한 번 Export
        try:
            export_res = ocr_helpers.system_export(timeout=10)
            out["export_ok"] = bool(export_res.get("dialog_handled") is not None
                                    or export_res.get("exp_files"))
            out["exp_file_count"] = len(export_res.get("exp_files", []))
        except Exception as e:
            out["export_error"] = str(e)

        # 판정
        all_ui_ok = all(r["ok"] for r in out["applied_results"])
        out["batch_ok"] = all_ui_ok and out["save_ok"] and out["export_ok"]

    finally:
        # baseline 복원 (다음 isolated phase 위해)
        try:
            restore_baseline()
        except Exception as e:
            out["restore_error"] = str(e)
        out["duration"] = time.time() - t0

    return out
