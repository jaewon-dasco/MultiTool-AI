"""chm.py — CHM 추출 및 버전 히스토리 파싱"""

import subprocess
from pathlib import Path


def extract_chm(chm_path: Path, out_dir: Path):
    """hh.exe -decompile로 CHM → HTM 파일 추출"""
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["hh.exe", "-decompile", str(out_dir), str(chm_path)],
        check=True, capture_output=True
    )


def parse_version_history(htm_dir: Path) -> list[dict]:
    """VersionDifferences.htm 파싱 → [{date, version, changes}, ...]"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("  [WARN] beautifulsoup4 미설치 — 버전 히스토리 파싱 skip")
        return []

    rows = []
    for f in htm_dir.glob("*ersion*ifference*.htm"):
        soup = BeautifulSoup(f.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        for tr in soup.select("table tr")[1:]:
            cells = [td.get_text(strip=True) for td in tr.select("td")]
            if len(cells) >= 3:
                rows.append({"date": cells[0], "version": cells[1], "changes": cells[2]})
    return rows
