#!/usr/bin/env python3
"""Vision helper — DESIGN DRAFT (not yet executed in recipes).

Use case:
- Recipe needs a UI element's coordinate that pywinauto can't reliably find
  (e.g. diagram nodes that have no UIA text label).
- Send current screenshot + intent to Mac mini Qwen3.5 27B for vision inference.
- Model returns proposed (x, y) and reasoning.
- Caller validates by clicking + checking expected side effect (XML sha change,
  floating toolbar appearance, etc.).
- On success, cache the (intent → coord) mapping in KB so next runs skip the LLM.

Trade-offs (2026-05-21 measured):
- Single vision call ≈ 150~180s (qwen3.5:27b Q4_K_M on Mac mini 32GB).
- Use sparingly: one-time learning → persist as recipe. Do not call per action.

Endpoint: https://macmini.tailed5292.ts.net:11434/api/generate
Model:    qwen3.5:27b (verified vision-capable 2026-05-21, replaced gemma4:26b)
"""
import base64
import json
import re
from pathlib import Path
from typing import Optional

import requests
import urllib3
urllib3.disable_warnings()

OLLAMA_URL = "https://macmini.tailed5292.ts.net:11434/api/generate"
MODEL = "qwen3.5:27b"
DEFAULT_TIMEOUT = 600  # 10 minutes - 27B vision inference is slow


def query_gemma_vision(
    image_path: Path,
    intent: str,
    schema_hint: str = '{"action": "<verb>", "x": <int>, "y": <int>, "reason": "<short>"}',
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Send screenshot + intent to the vision model, request structured action.

    Function name kept for backward compatibility; backend is now Qwen3.5 27B.
    Returns dict {ok, raw_response, parsed: dict | None, error}.
    """
    img_b64 = base64.b64encode(Path(image_path).read_bytes()).decode()
    prompt = (
        f"Role: You are a GUI automation assistant.\n"
        f"Intent: {intent}\n"
        f"Constraint: Look at the screenshot and return precise pixel coordinates. "
        f"Reply with ONLY this JSON schema, no other text: {schema_hint}"
    )
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
        "options": {"temperature": 0.1},
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=timeout, verify=False)
        r.raise_for_status()
        data = r.json()
        raw = data.get("response", "")
        parsed = _extract_json(raw)
        return {"ok": parsed is not None, "raw_response": raw, "parsed": parsed, "error": None}
    except Exception as e:
        return {"ok": False, "raw_response": None, "parsed": None, "error": str(e)}


def _extract_json(text: str) -> Optional[dict]:
    """Extract first JSON object from text (Gemma may surround with prose)."""
    if not text:
        return None
    # try direct parse first
    try:
        return json.loads(text)
    except Exception:
        pass
    # regex fallback: greedy block between first { and last }
    m = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


# === Recipe integration pattern (pseudo) ===
#
# from .common import connect, ensure_maximized
# from .gemma_vision_helper import query_gemma_vision
#
# def click_element_via_gemma(win, intent: str, screenshot_path: Path) -> bool:
#     win.capture_as_image().save(screenshot_path)
#     r = query_gemma_vision(screenshot_path, intent=intent)
#     if not r["ok"]:
#         return False
#     coords = (r["parsed"]["x"], r["parsed"]["y"])
#     # Side-effect check: capture before/after sha to verify the click did something
#     from pywinauto import mouse
#     mouse.click(coords=coords)
#     return True  # caller validates further with XML diff
#
# === Caching strategy ===
#
# Once a (intent, screen_fingerprint) → coords mapping is verified, write to
# skills/e2e_explorer/kb/coord_cache.jsonl so future recipe calls bypass Gemma.
# Cache key: hash of (intent text, window size, current panel state).


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m skills.e2e_explorer.gemma_vision_helper <image> <intent>")
        sys.exit(1)
    r = query_gemma_vision(Path(sys.argv[1]), sys.argv[2])
    print(json.dumps(r, ensure_ascii=False, indent=2))
