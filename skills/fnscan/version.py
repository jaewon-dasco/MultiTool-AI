"""version.py — 설치 버전 탐지 및 CHM 변경 감지"""

import hashlib
import json
from pathlib import Path

EPEC_ROOT    = Path(r"C:\Program Files (x86)\Epec")
VERSIONS_DIR = Path(__file__).parent.parent.parent / "docs" / "versions"


def get_installed_versions() -> dict[str, Path]:
    """MultiTool Creator 설치 폴더 열거 → {버전문자열: Path}"""
    return {
        p.name.split("MultiTool Creator ")[-1]: p
        for p in EPEC_ROOT.glob("MultiTool Creator *") if p.is_dir()
    }


def chm_md5(chm_path: Path) -> str | None:
    return hashlib.md5(chm_path.read_bytes()).hexdigest() if chm_path.exists() else None


def needs_update(ver: str, chm_path: Path) -> bool:
    """meta.json CHM MD5와 현재 파일 비교 → 재처리 필요 여부"""
    meta = VERSIONS_DIR / ver / "meta.json"
    if not meta.exists():
        return True
    stored = json.loads(meta.read_text())
    return stored.get("chm_md5") != chm_md5(chm_path)
