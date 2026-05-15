#!/usr/bin/env python3
"""Gemma vision helper — DESIGN DRAFT (not yet executed in recipes).

Use case:
- Recipe needs a UI element's coordinate that pywinauto can't reliably find
  (e.g. diagram nodes that have no UIA text label).
- Send current screenshot + intent to Mac mini Gemma4:26b for vision inference.
- Gemma returns proposed (x, y) and reasoning.
- Caller validates by clicking + checking expected side effect (XML sha change,
  floating toolbar appearance, etc.).
- On success, cache the (intent → coord) mapping in KB so next runs skip Gemma.

Trade-offs (2026-05-15 실측):
- Single Gemma vision call ≈ 70~120+ seconds (gemma4:26b on Mac mini).
- Use sparingly: 1회 학습 → recipe로 영구화. 매 액션마다 호출 금지.

Endpoint: https://macmini.tailed5292.ts.net:11434/api/generate
Model:    gemma4:26b (verified vision-capable 2026-05-15)
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
MODEL = "gemma4:26b"
DEFAULT_TIMEOUT = 300  # 5 minutes - vision inference is slow


def query_gemma_vision(
    image_path: Path,
    intent: str,
    schema_hint: str = '{"action": "<verb>", "x": <int>, "y": <int>, "reason": "<short>"}',
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Send screenshot + intent to Gemma, ask for structured action.

    Returns dict {ok, raw_response, parsed: dict | None, error}.
    """
    img_b64 = base64.b64encode(Path(image_path).read_bytes()).decode()
    prompt = (
        f"역할: 너는 GUI 자동화 도우미야.\n"
        f"의도: {intent}\n"
        f"제약: 화면을 보고 정확한 픽셀 좌표를 알려줘. "
        f"응답은 반드시 다음 JSON 스키마만 출력 (다른 텍스트 금지): {schema_hint}"
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
