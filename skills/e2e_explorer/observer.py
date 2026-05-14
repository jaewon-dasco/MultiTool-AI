""".mtproject·.exp 스냅샷 캡처 (읽기 전용).

원본 파일은 절대 수정하지 않음 — 복사 + 해시만.
"""
from __future__ import annotations

import hashlib
import logging
import shutil
import time
from pathlib import Path

log = logging.getLogger(__name__)


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_file(src: Path, out_dir: Path, label: str = "") -> dict | None:
    """단일 파일 스냅샷. out_dir/<timestamp>_<label>_<name> 로 복사."""
    if not src.exists():
        log.warning("snapshot src not found: %s", src)
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    suffix = f"_{label}" if label else ""
    target = out_dir / f"{ts}{suffix}_{src.name}"
    shutil.copy2(src, target)
    return {
        "src": str(src),
        "dst": str(target),
        "sha256": file_hash(target),
        "size": target.stat().st_size,
        "captured_at": time.time(),
    }


def snapshot_project(project_path: Path, out_dir: Path, label: str = "") -> dict:
    """`.mtproject` + 같은 폴더의 모든 `.exp` 스냅샷.

    project_path: `.mtproject` 파일 경로
    out_dir: 스냅샷 출력 디렉토리
    """
    out: dict = {"project": None, "exp_files": [], "label": label}
    if not project_path.exists():
        out["error"] = f"project not found: {project_path}"
        return out

    out["project"] = snapshot_file(project_path, out_dir, label=f"{label}_mtproject" if label else "mtproject")

    base = project_path.parent
    for exp in sorted(base.rglob("*.exp")):
        # _generated.exp 도 캡처 (관찰 대상)
        out["exp_files"].append(
            snapshot_file(exp, out_dir, label=f"{label}_exp" if label else "exp")
        )
    return out


def _cli() -> None:
    import argparse, json

    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO)
    r = snapshot_project(Path(args.project), Path(args.out), args.label)
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _cli()
