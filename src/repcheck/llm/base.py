"""Provider interface. Every backend (real API, mock, cache) implements `complete`."""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMError(Exception):
    """Any failure to obtain a usable model response."""


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def complete(self, system: str, user: str, cache_key: str | None = None) -> str:
        """Return the model's text reply. `cache_key` identifies the request for caching."""
