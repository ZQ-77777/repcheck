"""Response cache.

MockProvider    : replays saved responses only (no network) -> demos and tests.
CachingProvider : wraps a real provider; reuses a saved response or saves a new one.
Cache files: <cache_dir>/<cache_key>.json  {"cache_key", "model", "response"}
"""
from __future__ import annotations

import json
from pathlib import Path

from .base import LLMError, LLMProvider


def _path(cache_dir: Path, key: str) -> Path:
    return Path(cache_dir) / f"{key}.json"


class MockProvider(LLMProvider):
    name = "mock (cached responses)"

    def __init__(self, cache_dir: str | Path):
        self.cache_dir = Path(cache_dir)

    def complete(self, system: str, user: str, cache_key: str | None = None) -> str:
        if not cache_key:
            raise LLMError("Mock mode needs a cache key.")
        p = _path(self.cache_dir, cache_key)
        if not p.exists():
            raise LLMError(
                "Mock mode has no saved response for this PDF/table "
                f"(missing {p.name}). Use one of the example PDFs, or run once in live mode."
            )
        record = json.loads(p.read_text(encoding="utf-8"))
        self.name = f"mock: {record.get('model', 'unknown')}"
        return record["response"]


class CachingProvider(LLMProvider):
    def __init__(self, inner: LLMProvider, cache_dir: str | Path):
        self.inner, self.cache_dir = inner, Path(cache_dir)
        self.name = inner.name

    def complete(self, system: str, user: str, cache_key: str | None = None) -> str:
        if cache_key:
            p = _path(self.cache_dir, cache_key)
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))["response"]
        response = self.inner.complete(system, user, cache_key)
        if cache_key:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            _path(self.cache_dir, cache_key).write_text(
                json.dumps({"cache_key": cache_key, "model": self.inner.name, "response": response},
                           ensure_ascii=False, indent=2), encoding="utf-8")
        return response
