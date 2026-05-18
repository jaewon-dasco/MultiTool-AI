"""Central configuration. 환경변수 우선, JSON config 다음, hardcoded 마지막 fallback.

새 환경 이식 시:
1. 환경변수만 설정 → 즉시 작동
2. 또는 config.json 작성

ENV:
  E2E_ROOT                : project root directory
  E2E_PROJECT_FILE        : .mtproject path
  E2E_MULTITOOL_EXE       : MultiTool.exe path
  E2E_OLLAMA_URL          : Mac mini Gemma endpoint
  E2E_OLLAMA_MODEL        : model tag
  E2E_OLLAMA_TIMEOUT      : seconds
"""
import os, json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_DEFAULT_CONFIG_FILE = _HERE / "config.json"

_HARDCODED_DEFAULTS = {
    "root": str(_HERE.parents[1]),  # AI_MutiTool/
    "project_file": str(_HERE.parents[1] / "MultiToolProject" / "E2EProject" / "DasDemoProject.mtproject"),
    "multitool_exe": r"C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe",
    "multitool_manual_chm": r"C:\Program Files (x86)\Epec\MultiTool Creator 8.4\Resources\Manual.chm",
    "ollama_url": "https://macmini.tailed5292.ts.net:11434",
    "ollama_model": "gemma4:26b",
    "ollama_timeout": 300,
    "ocr_lang": "en-US",
    "max_cycles_default": 5,
    "logs_dir": str(_HERE.parents[1] / "logs" / "e2e"),
    "kb_dir": str(_HERE / "kb"),
    "sequences_dir": str(_HERE / "sequences"),
    "sequences_ui_dir": str(_HERE / "sequences_ui"),
}


def _load_json_config() -> dict:
    if _DEFAULT_CONFIG_FILE.exists():
        try:
            return json.loads(_DEFAULT_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception: pass
    return {}


_json_cfg = _load_json_config()


def get(key: str, default=None):
    """ENV > config.json > hardcoded default."""
    env_key = "E2E_" + key.upper()
    if env_key in os.environ:
        v = os.environ[env_key]
        # type coerce for known int keys
        if key in ("ollama_timeout", "max_cycles_default"):
            try: return int(v)
            except: pass
        return v
    if key in _json_cfg:
        return _json_cfg[key]
    if key in _HARDCODED_DEFAULTS:
        return _HARDCODED_DEFAULTS[key]
    return default


def all_config() -> dict:
    out = dict(_HARDCODED_DEFAULTS)
    out.update(_json_cfg)
    for k in _HARDCODED_DEFAULTS:
        env_v = os.environ.get("E2E_" + k.upper())
        if env_v is not None:
            out[k] = env_v
    return out


if __name__ == "__main__":
    import json as _j
    print(_j.dumps(all_config(), indent=2, ensure_ascii=False, default=str))
