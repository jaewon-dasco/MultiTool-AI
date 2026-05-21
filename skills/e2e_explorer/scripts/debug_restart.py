#!/usr/bin/env python3
"""Debug restart_multitool_clean — verbose phase tracing.

흐름:
1. MultiTool 새로 시작 + 프로젝트 로드
2. restart_multitool_clean() 호출, 각 phase 로그
3. 성공/실패 + 메시지
"""
import sys, time, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

MULTITOOL = r"C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe"


def log(msg): print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    log("=== Phase 0: clean start MultiTool ===")
    subprocess.Popen([MULTITOOL])
    time.sleep(25)

    log("Loading project via ui_open_project.py")
    r = subprocess.run([sys.executable, str(ROOT / "skills/e2e_explorer/scripts/ui_open_project.py")],
                       capture_output=True, text=True, timeout=60)
    log(f"  rc={r.returncode}, stdout tail: {r.stdout[-200:]!r}")

    time.sleep(3)

    log("=== Phase 1: connect check ===")
    from skills.e2e_explorer.recipes import common
    try:
        app, win = common.connect(timeout=5)
        log(f"  connect OK, win title: {win.window_text()[:60]!r}")
        h = common.find_hyperlink(win, "CU_3606_21_1")
        log(f"  hyperlink CU_3606_21_1: {'FOUND' if h else 'MISSING'}")
    except Exception as e:
        log(f"  connect FAIL: {e}")
        return 1

    log("=== Phase 2: call restart_multitool_clean ===")
    from skills.e2e_explorer.recipes.seed_runner_ui import restart_multitool_clean
    t0 = time.time()
    ok = restart_multitool_clean()
    dt = time.time() - t0
    log(f"  restart_multitool_clean() returned: {ok} (took {dt:.1f}s)")

    log("=== Phase 3: post-restart connect ===")
    try:
        app, win = common.connect(timeout=5)
        log(f"  connect OK, win title: {win.window_text()[:60]!r}")
        h = common.find_hyperlink(win, "CU_3606_21_1")
        log(f"  hyperlink CU_3606_21_1: {'FOUND' if h else 'MISSING'}")
    except Exception as e:
        log(f"  connect FAIL: {e}")

    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
