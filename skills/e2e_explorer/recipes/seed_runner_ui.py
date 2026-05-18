"""UI-channel seed runner: each seed → UI change → Ctrl+S → System Export → diff capture → restore.

핵심 흐름:
1. backup .mtproject + 모든 .exp (baseline)
2. UI 변경 (set_field_auto)
3. Ctrl+S (mtproject 저장)
4. mtproject diff 캡쳐
5. Ctrl+Alt+E (System Export)
6. .exp diff 캡쳐
7. KB 적재: {mtproject_diff, exp_diff}
8. restore (mtproject + .exp)

실패 시 failures.jsonl에 누적.
"""
import time, hashlib, json, shutil, traceback, difflib, re
from pathlib import Path
from . import common, ocr_helpers
from pywinauto.keyboard import send_keys

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")
ORIG_BAK = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject.bak.ui_exp_20260515_103230")
RUN_ROOT = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\logs\e2e\night_ui")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def quick_xml_diff(before_path: Path, after_path: Path, max_lines: int = 30) -> dict:
    b = before_path.read_text(encoding="utf-8", errors="replace").splitlines()
    a = after_path.read_text(encoding="utf-8", errors="replace").splitlines()
    diff = list(difflib.unified_diff(b, a, n=0, lineterm=""))
    removed = [ln[1:] for ln in diff if ln.startswith("-") and not ln.startswith("---")]
    added = [ln[1:] for ln in diff if ln.startswith("+") and not ln.startswith("+++")]
    val_changes = []
    for r_ln in removed:
        m = re.search(r"<(\w+)>([^<>]+)</\1>", r_ln)
        if not m: continue
        for a_ln in added:
            m2 = re.search(r"<(\w+)>([^<>]+)</\1>", a_ln)
            if m2 and m.group(1) == m2.group(1) and m.group(2) != m2.group(2):
                val_changes.append({"tag": m.group(1), "old": m.group(2), "new": m2.group(2)})
                break
    return {"raw_added": len(added), "raw_removed": len(removed),
            "value_changes": val_changes[:max_lines]}


def restore_baseline():
    """Restore .mtproject from original backup + remove all .exp files in E2EProject.

    Note: MultiTool은 메모리에 변경된 상태를 유지함. 파일만 복원해도 UI는 그대로.
    각 시드 시작 시 reload_multitool_project()를 추가로 호출해야 깨끗한 상태.
    """
    shutil.copy(ORIG_BAK, PROJ)
    for p in ocr_helpers.PROJ_DIR.rglob("*.exp"):
        try: p.unlink()
        except Exception: pass


def reload_multitool_project():
    """MultiTool에서 현재 프로젝트 닫고 재로드. 메모리 상태 깨끗해짐.
    Ctrl+W (close) → 'Don't Save' → Open Project... → 경로 + Enter.
    """
    try:
        app, win = common.connect()
        win.set_focus()
        time.sleep(0.3)
        # File > Close 또는 Ctrl+W (실제 단축키는 MultiTool 확인 필요)
        # 더 안전: ESC로 메뉴 닫기 + Network Editor 탭으로 강제 이동
        send_keys("{ESC}"); time.sleep(0.3)
        # Click Network Editor tab
        for t in win.descendants(control_type="TabItem"):
            if t.window_text() == "Network Editor":
                t.click_input(); time.sleep(0.5)
                break
        # Deselect canvas (빈 영역 클릭)
        common.deselect_diagram(win)
        time.sleep(0.5)
    except Exception:
        pass


def run_one_seed(seed: dict, label: str, value: str,
                 sidebar_tab: str | None = None,
                 cycle_idx: int = 0) -> dict:
    """단일 시드 실행. seed: {name, idx, label, value, tab?, type?}."""
    name = seed.get("name", "?")
    idx = seed.get("idx", 0)
    out_dir = RUN_ROOT / f"seed_{idx:02d}_{name}" / f"cycle_{cycle_idx:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    result = {"seed": name, "idx": idx, "cycle": cycle_idx, "label": label, "value": value,
              "tab": sidebar_tab, "ok": False, "phase": "init", "log": []}

    def log(msg): result["log"].append(msg); print(f"  [seed {idx:02d} c{cycle_idx} {name}] {msg}")

    try:
        # 1. Restore baseline + reload MultiTool view
        restore_baseline()
        time.sleep(0.5)
        reload_multitool_project()
        result["phase"] = "baseline_restored"

        # Snapshot before
        before_mt_sha = sha(PROJ)[:16]
        result["before_mt_sha"] = before_mt_sha
        bef_mt_copy = out_dir / "00_baseline.mtproject"
        shutil.copy(PROJ, bef_mt_copy)

        # Reopen MultiTool view: ensure CAN tab is active if needed (some tabs need switching)
        app, win = common.connect()
        common.ensure_maximized(win)

        # 사이드바 탭이 요청되면 먼저 디바이스 Configure 패널 진입 필요
        if sidebar_tab:
            from .field_change import click_left_tab, open_configure_panel
            # First: open device configure (디바이스 클릭 → 렌치)
            opened = open_configure_panel(win, "CU_3606_21_1")
            if not opened:
                result["phase"] = "configure_panel_failed"; log("FAIL: Configure panel"); return result
            time.sleep(0.8)
            if not click_left_tab(win, sidebar_tab):
                result["phase"] = "tab_switch_failed"; log(f"FAIL: tab '{sidebar_tab}'")
                return result
            log(f"Configure+tab='{sidebar_tab}'")
        result["phase"] = "tab_ready"

        # 2. UI change via OCR — actions 시퀀스 지원 (mode 설정 → property 설정)
        actions_list = seed.get("actions")
        if actions_list:
            # 다중 액션 (예: Pin mode → Properties)
            action_results = []
            all_ok = True
            for ai, a in enumerate(actions_list):
                # 표 행 처리: 라벨이 표의 row marker (예: "VAVLE_UP") + column이 'Modes'
                col = a.get("column")
                if col:
                    # 표 행에서 컬럼 셀 클릭 후 입력
                    coords = ocr_helpers.click_table_cell(a["label"], col)
                    if not coords:
                        action_results.append({"step": ai, "ok": False, "reason": f"table_cell {a['label']}×{col} not found"})
                        all_ok = False; break
                    if a.get("value"):
                        # Combo 또는 Text 입력
                        if a.get("kind") == "combobox":
                            time.sleep(0.5)
                            # 드롭다운 항목 OCR
                            ocr2 = ocr_helpers.ocr_screen()
                            v = a["value"].lower()
                            cands = [it for it in ocr2 if v in it["text"].lower()]
                            if cands:
                                cands.sort(key=lambda it: it["y"])
                                from pywinauto import mouse
                                mouse.click(coords=(cands[0]["xc"], cands[0]["yc"]))
                                time.sleep(0.5)
                            else:
                                send_keys(a["value"] + "{ENTER}")
                        else:
                            send_keys("^a"); send_keys("{DELETE}")
                            send_keys(a["value"], with_spaces=True); send_keys("{TAB}")
                    action_results.append({"step": ai, "ok": True, "kind": "table_cell"})
                else:
                    # 일반 라벨 옆 컨트롤
                    sub = ocr_helpers.set_field_auto(a["label"], a.get("value", ""), expected_kind=a.get("kind"))
                    action_results.append({"step": ai, **sub})
                    if not sub["ok"]:
                        all_ok = False; break
                time.sleep(0.5)
            action = {"ok": all_ok, "kind": "sequence", "action": f"{len(actions_list)} actions",
                      "steps": action_results}
        else:
            # 단일 액션 (kind별 분기)
            expected_kind = seed.get("expected_kind")
            if expected_kind == "toolbar_action":
                ok = ocr_helpers.click_toolbar_button(win, label)
                action = {"ok": ok, "kind": "toolbar_action",
                          "action": f"toolbar.click '{label}'"}
            elif expected_kind == "toolbar_action_with_dialog":
                ok = ocr_helpers.click_toolbar_button(win, label)
                action = {"ok": ok, "kind": "toolbar_action_with_dialog",
                          "action": f"toolbar.click '{label}' + dialog"}
                if ok and seed.get("dialog"):
                    time.sleep(1.5)
                    # 다이얼로그 처리 — 정확한 title은 모르므로 첫 발견 dialog
                    from pywinauto import Desktop
                    dlg_info = None
                    for w in Desktop(backend="win32").windows():
                        try:
                            t = w.window_text() or ""
                            if t and "MultiTool Creator" not in t and len(t) < 80:
                                dlg_info = {"hwnd": w.handle, "rect": w.rectangle(), "window": w}
                                break
                        except Exception: pass
                    if dlg_info:
                        fill_result = ocr_helpers.fill_dialog_form(dlg_info, seed["dialog"])
                        action["dialog_fill"] = fill_result
                        # OK 또는 확인 클릭
                        ocr_helpers.click_dialog_button(dlg_info, "OK") or ocr_helpers.click_dialog_button(dlg_info, "Yes")
                        time.sleep(1)
            elif expected_kind == "shortcut":
                send_keys(seed.get("shortcut", "")); time.sleep(1)
                action = {"ok": True, "kind": "shortcut", "action": f"sent '{seed['shortcut']}'"}
            elif expected_kind == "table_link":
                ok = ocr_helpers.click_toolbar_button(win, label) is not None
                action = {"ok": ok, "kind": "table_link", "action": "table link click"}
            elif expected_kind == "device_panel_x_button":
                # 디바이스 패널 좌측 Devices 리스트의 X 버튼 클릭
                from .device_disconnect import device_disconnect_from_network
                target = seed.get("target", "CU_3606_21_1")
                r = device_disconnect_from_network("NETWORK1", target, save=False)
                action = {"ok": r["ok"], "kind": "device_panel_x_button",
                          "action": f"disconnect {target}"}
            else:
                action = ocr_helpers.set_field_auto(label, value, expected_kind=expected_kind)
        result["detected_kind"] = action.get("kind")
        result["action"] = action.get("action")
        if not action["ok"]:
            result["phase"] = "ui_change_failed"; log(f"FAIL UI change: kind={action.get('kind')} action={action.get('action')}")
            return result
        log(f"UI changed via {action['action']}")
        result["phase"] = "ui_changed"

        # 3. Save mtproject (Ctrl+S)
        common.save_project()
        log("Ctrl+S saved")
        result["phase"] = "saved"

        # 4. mtproject diff
        after_mt_sha = sha(PROJ)[:16]
        result["after_mt_sha"] = after_mt_sha
        result["mt_size_delta"] = PROJ.stat().st_size - bef_mt_copy.stat().st_size
        aft_mt_copy = out_dir / "01_after_save.mtproject"
        shutil.copy(PROJ, aft_mt_copy)
        result["mt_diff"] = quick_xml_diff(bef_mt_copy, aft_mt_copy)
        log(f"mtproject: {before_mt_sha[:12]}→{after_mt_sha[:12]} Δ={result['mt_size_delta']:+d} value_changes={len(result['mt_diff']['value_changes'])}")

        # 5. .exp baseline snapshot (before Export)
        exp_before = ocr_helpers.snapshot_exp_state()  # 보통 비어있음 (restore에서 삭제됨)

        # 6. System Export (Ctrl+Alt+E)
        export_res = ocr_helpers.system_export(timeout=5)
        result["phase"] = "exported"
        log(f"export done · {len(export_res['exp_files'])} exp files generated · dialog={export_res['dialog_handled']}")

        # 7. .exp diff
        exp_diff = ocr_helpers.diff_exp_state(exp_before, export_res["exp_files"])
        result["exp_diff"] = exp_diff
        log(f"exp: +{len(exp_diff['added'])} ~{len(exp_diff['changed'])} -{len(exp_diff['removed'])}")
        # Save .exp copies
        for e in export_res["exp_files"]:
            src = ocr_helpers.PROJ_DIR / e["name"]
            dst = out_dir / f"02_after_export_{e['name'].replace(chr(92),'_').replace('/','_')}"
            try: shutil.copy(src, dst)
            except Exception: pass

        result["ok"] = True
        result["phase"] = "complete"
        return result

    except Exception as e:
        result["phase"] = result.get("phase", "?") + "_exception"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        log(f"EXCEPTION at phase={result['phase']}: {e}")
        return result
    finally:
        # 8. Always restore
        try:
            restore_baseline()
            log("restored")
        except Exception as e:
            log(f"restore FAIL: {e}")


def append_failure(failure: dict, fail_log: Path):
    fail_log.parent.mkdir(parents=True, exist_ok=True)
    with fail_log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(failure, ensure_ascii=False, default=str) + "\n")


def run_seeds_batch(seeds: list, cycles: int = 5, save_results: bool = True) -> dict:
    """N개 시드 × cycles회 실행."""
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    fail_log = RUN_ROOT / "failures.jsonl"
    results_log = RUN_ROOT / "results.jsonl"
    stats = {"total": 0, "success": 0, "failed": 0, "by_kind": {}, "by_phase_failure": {}}

    for cycle_idx in range(cycles):
        for seed in seeds:
            stats["total"] += 1
            r = run_one_seed(
                seed=seed,
                label=seed["label"],
                value=seed["value"],
                sidebar_tab=seed.get("tab"),
                cycle_idx=cycle_idx,
            )
            if save_results:
                with results_log.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({k:v for k,v in r.items() if k != "traceback"},
                                       ensure_ascii=False, default=str) + "\n")
            if r["ok"]:
                stats["success"] += 1
                kind = r.get("detected_kind", "?")
                stats["by_kind"][kind] = stats["by_kind"].get(kind, 0) + 1
            else:
                stats["failed"] += 1
                stats["by_phase_failure"][r["phase"]] = stats["by_phase_failure"].get(r["phase"], 0) + 1
                append_failure(r, fail_log)
    return stats
