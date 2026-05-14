"""Mac mini 원격 Ollama gemma4:26b 클라이언트.

JSON 강제·재시도·keep-alive 8h. v0.1 관찰 모드에서 사용.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

log = logging.getLogger(__name__)

DEFAULT_BASE = "https://macmini.tailed5292.ts.net:11434"
DEFAULT_MODEL = "gemma4:26b"


class OllamaClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE,
        model: str = DEFAULT_MODEL,
        timeout: int = 180,
        keep_alive: str = "8h",
        num_ctx: int = 16384,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.keep_alive = keep_alive
        self.num_ctx = num_ctx
        self.session = requests.Session()

    def health(self) -> bool:
        """`/api/tags` 응답 + 모델 존재 확인."""
        try:
            r = self.session.get(f"{self.base_url}/api/tags", timeout=15)
            r.raise_for_status()
            models = [m.get("name") for m in r.json().get("models", [])]
            return self.model in models
        except Exception as e:
            log.warning("health check failed: %s", e)
            return False

    @retry(
        retry=retry_if_exception_type((requests.RequestException,)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        reraise=True,
    )
    def chat(
        self,
        messages: list[dict],
        json_mode: bool = False,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Gemma4 chat API 호출.

        반환: {content, thinking, raw}
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {"temperature": temperature, "num_ctx": self.num_ctx},
        }
        if json_mode:
            payload["format"] = "json"

        r = self.session.post(
            f"{self.base_url}/api/chat", json=payload, timeout=self.timeout
        )
        r.raise_for_status()
        data = r.json()
        msg = data.get("message", {})
        return {
            "content": msg.get("content", ""),
            "thinking": msg.get("thinking", ""),
            "raw": data,
        }

    def observe(self, system_prompt: str, observation: dict) -> dict[str, Any]:
        """관찰 모드 전용 — 시스템 프롬프트 + JSON 관찰 데이터 → Gemma 응답."""
        obs_text = json.dumps(observation, ensure_ascii=False)[:50000]
        return self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": obs_text},
            ],
            json_mode=False,  # reasoning + 자연어 응답 허용
            temperature=0.3,
        )


def _cli() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--ping", action="store_true")
    ap.add_argument("--message", default="Reply with: PONG")
    args = ap.parse_args()

    c = OllamaClient()
    if args.ping:
        ok = c.health()
        print(f"health: {ok}")
        if not ok:
            return
    r = c.chat([{"role": "user", "content": args.message}])
    print("content:", r["content"])
    if r["thinking"]:
        print("thinking:", r["thinking"][:200])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _cli()
