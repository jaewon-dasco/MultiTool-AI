"""Verified seeds 영속 저장 — Phase 1 batch 대상 결정.

verified_seeds.json: {seed_name: pass_count}
pass_count >= MIN_VERIFIED 이면 다음 cycle batch에 포함.
isolated cycle에서 OK → pass_count += 1
batch에서 fail OR isolated에서 fail → pass_count = 0 (재검증 시작)
"""
import json
from pathlib import Path

KB_DIR = Path(__file__).resolve().parents[1] / "kb"
STORE_PATH = KB_DIR / "verified_seeds.json"
MIN_VERIFIED = 1  # 1번 isolated 통과 시 verified로 승급


def load_verified() -> dict:
    if STORE_PATH.exists():
        try:
            return json.loads(STORE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_verified(d: dict) -> None:
    KB_DIR.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def is_verified(name: str, store: dict | None = None) -> bool:
    s = store if store is not None else load_verified()
    return s.get(name, 0) >= MIN_VERIFIED


def promote(name: str, store: dict) -> None:
    """isolated cycle OK → pass_count += 1"""
    store[name] = store.get(name, 0) + 1


def demote(name: str, store: dict) -> None:
    """batch/isolated fail → 0으로 리셋"""
    store[name] = 0


def split_by_verified(seeds: list, store: dict | None = None) -> tuple[list, list]:
    """seeds → (verified_for_batch, unverified_for_isolated)"""
    s = store if store is not None else load_verified()
    batch = [seed for seed in seeds if is_verified(seed["name"], s)]
    isolated = [seed for seed in seeds if not is_verified(seed["name"], s)]
    return batch, isolated
