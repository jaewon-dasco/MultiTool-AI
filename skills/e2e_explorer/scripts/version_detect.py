#!/usr/bin/env python3
"""Detect MultiTool + .mtproject version markers for KB invalidation logic."""
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

PROJ_DEFAULT = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool\MultiToolProject\E2EProject\DasDemoProject.mtproject")
EXE_DEFAULT = r"C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe"


def get_versions(proj_path: Path = PROJ_DEFAULT, exe_path: str = EXE_DEFAULT) -> dict:
    """Return dict with: tool, sdk, system_version, exe_file_version."""
    out = {"tool": None, "sdk": None, "system_version": None, "exe_file_version": None}
    if proj_path.exists():
        try:
            root = ET.parse(proj_path).getroot()
            def lt(e): return e.tag.split('}')[-1]
            def find_first(node, tag):
                for c in node:
                    if lt(c) == tag: return c
                    r = find_first(c, tag)
                    if r is not None: return r
                return None
            for key, tag in [("system_version", "SystemVersion"), ("sdk", "SDK"), ("tool", "Tool")]:
                el = find_first(root, tag)
                if el is not None: out[key] = el.text
        except Exception: pass
    try:
        r = subprocess.run(
            ["powershell", "-Command", f'(Get-Item "{exe_path}").VersionInfo.FileVersion'],
            capture_output=True, text=True, timeout=5)
        v = r.stdout.strip()
        if v: out["exe_file_version"] = v
    except Exception: pass
    return out


def version_signature(versions: dict) -> str:
    """Compact signature for KB version comparison (e.g. 'MT8.4.9308.1109_SV1.0.13')."""
    tool = versions.get("tool") or versions.get("exe_file_version") or "unknown"
    sv = versions.get("system_version") or "unknown"
    return f"MT{tool}_SV{sv}"


if __name__ == "__main__":
    import json
    v = get_versions()
    print(json.dumps(v, indent=2, ensure_ascii=False))
    print(f"signature: {version_signature(v)}")
