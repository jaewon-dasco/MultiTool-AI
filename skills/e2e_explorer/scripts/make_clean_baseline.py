#!/usr/bin/env python3
"""Baseline 정합화 — MultiTool 로드 후 즉시 Ctrl+S → 새 baseline 백업 생성.

목적: 디바이스/네트워크/CAN 등 MultiTool 내부 자동 동기화로 인한
post-load 변경이 'baseline' 자체에 반영된 상태를 만들어, 야간 사이클에서
첫 save 시 noise 28건이 발생하지 않도록 함.
"""
import sys, time, shutil, hashlib
from pathlib import Path
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills.e2e_explorer.recipes import common

PROJ = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")
NEW_BAK = PROJ.parent / f"DasDemoProject.mtproject.bak.clean_baseline_{time.strftime('%Y%m%d_%H%M%S')}"


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main():
    app, win = common.connect()
    common.ensure_maximized(win)
    time.sleep(1.0)

    before_sha = sha(PROJ); before_size = PROJ.stat().st_size
    print(f"Before: sha={before_sha} size={before_size}")

    print("Sending Ctrl+S...")
    win.set_focus(); time.sleep(0.5)
    send_keys("^s")
    time.sleep(4.0)  # save 충분히 대기

    after_sha = sha(PROJ); after_size = PROJ.stat().st_size
    print(f"After:  sha={after_sha} size={after_size}")

    if before_sha == after_sha:
        print("⚠ 변화 없음 — MultiTool이 save를 안 했거나 이미 정합 상태")
    else:
        print(f"변경 감지 Δsize={after_size - before_size:+d}")

    shutil.copy(PROJ, NEW_BAK)
    print(f"새 baseline: {NEW_BAK.name}")
    print(f"  sha = {sha(NEW_BAK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
