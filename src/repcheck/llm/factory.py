"""Choose a provider from a mode string: 'mock' or 'live'."""
from __future__ import annotations

import os
from pathlib import Path

from .base import LLMError, LLMProvider
from .cache import CachingProvider, MockProvider
from .openai_compat import OpenAICompatibleProvider

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CACHE_DIR = PROJECT_ROOT / "examples" / "cache"


def load_dotenv_if_present() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")   # explicit path: works from any working directory
    except ImportError:  # python-dotenv is optional; plain environment variables also work
        pass


def default_mode() -> str:
    load_dotenv_if_present()
    return os.getenv("LLM_PROVIDER", "live" if os.getenv("API_KEY") else "mock").lower()


def get_provider(mode: str | None = None, cache_dir: str | Path | None = None) -> LLMProvider:
    load_dotenv_if_present()
    mode = (mode or default_mode()).lower()
    cache_dir = Path(cache_dir or os.getenv("CACHE_DIR", DEFAULT_CACHE_DIR))
    if mode == "mock":
        return MockProvider(cache_dir)
    if mode == "live":
        return CachingProvider(OpenAICompatibleProvider.from_env(), cache_dir)
    raise LLMError(f"Unknown provider mode '{mode}'. Use 'mock' or 'live'.")
