"""run.py — FunctionScan 전체 순차 실행 진입점"""

import json
import datetime
from pathlib import Path

from version import VERSIONS_DIR, EPEC_ROOT, get_installed_versions, chm_md5, needs_update
from chm     import extract_chm, parse_version_history
from uitree  import dump_ui_tree
from mapper  import build_function_map
from diff    import diff_function_maps, print_diff_report


def run():
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    installed = get_installed_versions()
    if not installed:
        print(f"[ERROR] MultiTool Creator 설치 버전 없음: {EPEC_ROOT}")
        return

    for ver, inst_path in installed.items():
        chm     = inst_path / "Resources" / "Manual.chm"
        ver_dir = VERSIONS_DIR / ver

        if not needs_update(ver, chm):
            print(f"[SKIP] {ver} — 변경 없음")
            continue

        print(f"[RUN]  {ver}")

        # CHM 추출
        if chm.exists():
            extract_chm(chm, ver_dir / "chm_extracted")
            history = parse_version_history(ver_dir / "chm_extracted")
            if history:
                (ver_dir / "version_history.json").write_text(
                    json.dumps(history, ensure_ascii=False, indent=2)
                )
        else:
            print("  [WARN] CHM 없음 — 추출 skip")

        # UIA 트리 덤프
        ts        = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        tree_path = ver_dir / "ui_tree" / f"ui_tree_{ts}.json"
        dump_ui_tree(ver, tree_path)

        # function_map 빌드
        fmap_prev = VERSIONS_DIR / f"{ver}_prev" / "function_map.json"
        fmap_path = ver_dir / "function_map.json"
        build_function_map(json.loads(tree_path.read_text()), fmap_path)

        # diff
        diff = diff_function_maps(fmap_prev, fmap_path)
        (ver_dir / "diff.json").write_text(json.dumps(diff, ensure_ascii=False, indent=2))
        print_diff_report(diff)

        # meta 저장
        (ver_dir / "meta.json").write_text(json.dumps({
            "version":   ver,
            "chm_md5":   chm_md5(chm),
            "dumped_at": ts,
            "tree_file": str(tree_path)
        }, indent=2))
        print(f"  -> {fmap_path}")


if __name__ == "__main__":
    run()
