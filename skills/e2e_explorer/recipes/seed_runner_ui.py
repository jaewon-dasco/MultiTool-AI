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
ORIG_BAK = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject.bak.clean_baseline")
# 2026-05-19: 노이즈 28건 → 0건 정합 baseline (MultiTool 로드 직후 save한 결과). 이전 ui_exp_20260515_103230는 pre-save 상태로 첫 save에서 13696B 자동 정합 변경 유발했음.
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


MULTITOOL_EXE = r"C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe"


def restart_multitool_clean():
    """야간 사이클: 시드 시작 전 MultiTool을 완전히 종료하고 재시작.

    이유: 메모리 누적 노이즈가 134/134 run에 동일하게 나타남 → 파일 복원만으로
    부족, 프로세스 자체를 재시작해야 깨끗한 baseline.

    절차:
      1. Alt+F4 → "Don't Save" (변경 폐기, mt_proj 파일 보존)
      2. 프로세스 종료 대기 (최대 8초)
      3. 잔존 프로세스가 있으면 win32 backend로 close
      4. Start MultiTool.exe + DasDemoProject.mtproject 경로 인자
      5. Splash 대기 (12초) + connect 시도
    """
    import subprocess
    from pywinauto import Application, Desktop
    # 1. Alt+F4 + 다이얼로그 처리
    try:
        app, win = common.connect(timeout=3)
        win.set_focus(); time.sleep(0.3)
        send_keys("%{F4}"); time.sleep(1.5)
        # "Don't Save" 다이얼로그: win32 backend, 좌표 클릭
        # MultiTool "Save Changes?" 다이얼로그는 [Save] [Don't Save] [Cancel] 3버튼 — 중앙(Don't Save) 클릭
        from pywinauto import mouse
        for w in Desktop(backend="win32").windows():
            try:
                title = w.window_text() or ""
                if "Save" in title or "MultiTool" in title:
                    r = w.rectangle()
                    # 3버튼 중앙 = right - ~145 → "Don't Save" (Confirm 다이얼로그와 다른 layout)
                    # 안전한 키보드 단축키: Alt+N (Don't Save 단축키)
                    mouse.click(coords=(r.left + r.width()//2, r.top + r.height()//2))
                    break
            except Exception: pass
        send_keys("%n"); time.sleep(2.0)  # Alt+N = Don't Save
    except Exception:
        pass
    # 2. 프로세스 종료 대기
    for _ in range(8):
        try:
            Application(backend="uia").connect(title_re=".*MultiTool Creator.*", timeout=1)
            time.sleep(1)
        except Exception:
            break
    else:
        # 잔존 프로세스 강제 종료 (메모리 룰: Stop-Process 금지지만 야간 사이클의 폴백)
        try:
            subprocess.run(["taskkill", "/IM", "MultiTool.exe", "/F"],
                           capture_output=True, timeout=5)
        except Exception: pass
        time.sleep(2)
    # 3. 재시작 (인자 전달이 무시되므로 StartPage 거쳐 Open Project 자동화)
    try:
        subprocess.Popen([MULTITOOL_EXE])
    except Exception as e:
        print(f"  [restart] Popen FAIL: {e}")
        return False
    # 4. Splash + connect 대기
    win = None
    for attempt in range(15):
        time.sleep(2)
        try:
            app, win = common.connect(timeout=2)
            common.ensure_maximized(win)
            time.sleep(1.5)
            break
        except Exception:
            continue
    if win is None:
        print("  [restart] connect FAIL after 30s")
        return False
    # 5. 프로젝트 이미 로드되었는지(디바이스 Hyperlink 존재) 확인
    try:
        if common.find_hyperlink(win, "CU_3606_21_1"):
            return True
    except Exception: pass
    # 6. StartPage의 'Open Project...' Hyperlink 클릭 → 경로 입력 → Enter
    open_link = None
    try:
        for h in win.descendants(control_type="Hyperlink"):
            try:
                if "Open Project" in h.window_text():
                    open_link = h; break
            except Exception: pass
    except Exception: pass
    if open_link is None:
        print("  [restart] Open Project Hyperlink not found")
        return False
    try:
        if hasattr(open_link, "invoke"): open_link.invoke()
        else: open_link.click_input()
    except Exception as e:
        print(f"  [restart] open_link click FAIL: {e}")
        return False
    time.sleep(2.0)
    # File dialog: path + Enter
    send_keys(str(PROJ).replace(" ", "{SPACE}"), pause=0.02)
    time.sleep(0.5)
    send_keys("{ENTER}")
    time.sleep(8)
    # 7. 로드 확인 — 디바이스 hyperlink 보이면 OK
    try:
        app, win = common.connect(timeout=3)
        common.ensure_maximized(win)
        for _ in range(8):
            if common.find_hyperlink(win, "CU_3606_21_1"):
                return True
            time.sleep(1.5)
    except Exception: pass
    print("  [restart] project load verification FAIL")
    return False


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
        # 1. Restore baseline (파일) + MultiTool 완전 재시작 (메모리 클린)
        restore_baseline()
        time.sleep(0.5)
        if not restart_multitool_clean():
            result["phase"] = "multitool_restart_failed"; log("FAIL: restart"); return result
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
            elif expected_kind == "io_mode_button":
                # I/O 핀 모드 변경 — UIA 기반 (label=핀번호, value=모드short)
                from .io_pin_recipe import set_pin_mode
                action = set_pin_mode(win, pin_id=label, mode_short=value,
                                       connector=seed.get("connector", "1"))
            elif expected_kind == "io_variable_name":
                # I/O 핀 변수명 변경 — 셀 더블클릭 → 우측 Edit (label=핀번호, value=새 이름)
                from .io_pin_recipe import set_pin_variable_name
                action = set_pin_variable_name(win, pin_id=label, new_name=value,
                                                connector=seed.get("connector", "1"))
            elif expected_kind == "network_property":
                # NETWORK 노드 속성 변경 — 현재 BitRate만 지원
                from .network_property import set_network_bitrate
                target = seed.get("target_network", "NETWORK1")
                action = set_network_bitrate(win, network_name=target, value=value)
            else:
                action = ocr_helpers.set_field_auto(label, value, expected_kind=expected_kind,
                                                     table_column=seed.get("table_column"))
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
