"""LLM 추상화 — Ollama·OpenAI·Anthropic 등 backend 교체 가능.

API key·URL은 모두 config.py를 통해 환경변수에서 읽음.
새 backend 추가 시: BaseLLMClient를 상속하여 observe/generate 구현.
"""
import base64
import json
from abc import ABC, abstractmethod
from pathlib import Path
import requests
import urllib3
urllib3.disable_warnings()

from . import config


class BaseLLMClient(ABC):
    @abstractmethod
    def observe(self, system_prompt: str, payload: dict, timeout: int = None) -> dict:
        """payload 분석 + 자연어 응답. Returns: {content, thinking?, raw?}."""
        ...

    @abstractmethod
    def vision(self, image_path: str, prompt: str, timeout: int = None) -> dict:
        """이미지 + 프롬프트 → 응답. Returns: {content}."""
        ...

    def health(self) -> bool:
        try:
            r = self.observe("ping", {"q": "ok"}, timeout=10)
            return bool(r.get("content"))
        except Exception:
            return False


class OllamaClient(BaseLLMClient):
    def __init__(self, url: str = None, model: str = None, timeout: int = None):
        self.url = url or config.get("ollama_url")
        self.model = model or config.get("ollama_model")
        self.timeout = timeout or config.get("ollama_timeout", 300)

    def observe(self, system_prompt: str, payload: dict, timeout: int = None) -> dict:
        prompt = system_prompt + "\n\n[Payload]\n" + json.dumps(payload, ensure_ascii=False)[:4000]
        r = requests.post(
            f"{self.url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": 0.1}},
            timeout=timeout or self.timeout, verify=False)
        r.raise_for_status()
        data = r.json()
        return {"content": data.get("response", ""), "thinking": ""}

    def vision(self, image_path: str, prompt: str, timeout: int = None) -> dict:
        img_b64 = base64.b64encode(Path(image_path).read_bytes()).decode()
        r = requests.post(
            f"{self.url}/api/generate",
            json={"model": self.model, "prompt": prompt, "images": [img_b64],
                  "stream": False, "options": {"temperature": 0.1}},
            timeout=timeout or self.timeout, verify=False)
        r.raise_for_status()
        return {"content": r.json().get("response", "")}


class NoOpClient(BaseLLMClient):
    """--no-llm 모드용. LLM 없이 동작."""
    def observe(self, system_prompt, payload, timeout=None):
        return {"content": "", "thinking": ""}
    def vision(self, image_path, prompt, timeout=None):
        return {"content": ""}
    def health(self):
        return True


def get_client(backend: str = "ollama") -> BaseLLMClient:
    if backend == "ollama":
        return OllamaClient()
    if backend == "noop":
        return NoOpClient()
    raise ValueError(f"unknown backend: {backend}")
