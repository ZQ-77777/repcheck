"""Any OpenAI-compatible chat-completions endpoint (OpenAI, DeepSeek, Azure-style proxies...).

Uses only the standard library so the project has no SDK dependency.
Configuration (environment or .env): API_KEY, BASE_URL, MODEL.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .base import LLMError, LLMProvider

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, model: str = DEFAULT_MODEL,
                 timeout: int = 120, temperature: float = 0.0):
        if not api_key:
            raise LLMError("API_KEY is not set. Add it to .env, or run in mock mode.")
        self.api_key, self.base_url, self.model = api_key, base_url.rstrip("/"), model
        self.timeout, self.temperature = timeout, temperature
        self.name = model

    @classmethod
    def from_env(cls) -> "OpenAICompatibleProvider":
        return cls(api_key=os.getenv("API_KEY", ""),
                   base_url=os.getenv("BASE_URL", DEFAULT_BASE_URL),
                   model=os.getenv("MODEL", DEFAULT_MODEL))

    def _post(self, payload: dict) -> dict:
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions", data=json.dumps(payload).encode(), method="POST",
            # Both header styles: OpenAI-style gateways read Authorization, Azure API Management
            # gateways such as the HKUST GenAI service read api-key.
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}",
                     "api-key": self.api_key},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode())

    def complete(self, system: str, user: str, cache_key: str | None = None) -> str:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        try:
            data = self._post(payload)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            # Some reasoning models (e.g. the GPT-5 family) only accept the default temperature.
            if exc.code == 400 and "temperature" in detail.lower():
                payload.pop("temperature")
                try:
                    data = self._post(payload)
                except urllib.error.HTTPError as exc2:
                    detail2 = exc2.read().decode(errors="replace")[:300]
                    raise LLMError(f"API returned HTTP {exc2.code}: {detail2}") from exc2
                except (urllib.error.URLError, TimeoutError) as exc2:
                    raise LLMError(f"Could not reach {self.base_url}: {exc2}") from exc2
            else:
                raise LLMError(f"API returned HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise LLMError(f"Could not reach {self.base_url}: {exc}") from exc
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected API response format: {str(data)[:300]}") from exc
