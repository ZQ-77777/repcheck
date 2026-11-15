"""M3 — Ask the model for structured output and parse it.

The model is used for exactly two tasks:
  extract_spec          : checklist fields with page evidence   (stage 1)
  extract_table_numbers : printed numbers of the target table   (stage 2)
Everything the model returns is checked afterwards by verifier.py / table_numbers.py.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .checklist_templates import FieldSpec
from .llm.base import LLMError, LLMProvider
from .schemas import Context, Page, TableTarget

PROMPT_DIR = Path(__file__).parent / "llm" / "prompts"
PROMPT_VERSION = "v1"      # bump when a prompt changes, so old cache entries are not reused


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / f"{name}_{PROMPT_VERSION}.txt").read_text(encoding="utf-8")


def make_cache_key(task: str, content_hash: str, table: TableTarget, template: str = "") -> str:
    parts = [task, content_hash[:12], f"table{table.number}", template, PROMPT_VERSION]
    return "_".join(p for p in parts if p)


class ResponseFormatError(LLMError):
    """The model answered, but not with usable JSON."""


def parse_json_response(text: str) -> dict:
    """Accept bare JSON or JSON wrapped in ``` fences / short prose."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise ResponseFormatError(f"Model reply contains no JSON object: {text[:200]!r}")
    try:
        return json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ResponseFormatError(f"Model reply is not valid JSON ({exc}).") from exc


def _pages_block(chunks: list) -> str:
    return "\n\n".join(f"[p.{n}]\n{text}" for n, text in chunks)


def _call_json(provider: LLMProvider, system: str, user: str, cache_key: str) -> dict:
    """One retry with a different cache key if the first reply cannot be parsed."""
    try:
        return parse_json_response(provider.complete(system, user, cache_key))
    except ResponseFormatError:
        retry_user = user + "\n\nYour previous reply was not valid JSON. Return valid JSON only."
        return parse_json_response(provider.complete(system, retry_user, cache_key + "_retry"))


def spec_user_prompt(context: Context, fields: list[FieldSpec]) -> str:
    field_lines = "\n".join(
        f'- "{f.key}"{" (LIST)" if f.is_list else ""}: {f.description}' for f in fields)
    t = context.target
    return (f"Target table: {t.label} — {t.caption}\n"
            f"The table is on page(s) {', '.join(map(str, t.pages))}.\n\n"
            f"Fields to fill:\n{field_lines}\n\nPaper pages:\n\n{_pages_block(context.chunks)}")


def extract_spec(context: Context, fields: list[FieldSpec], provider: LLMProvider,
                 cache_key: str) -> dict:
    data = _call_json(provider, load_prompt("extract_spec"), spec_user_prompt(context, fields), cache_key)
    if not isinstance(data.get("fields"), dict):
        raise LLMError("Model reply has no 'fields' object.")
    return data


def extract_table_numbers(target: TableTarget, pages: list[Page], provider: LLMProvider,
                          cache_key: str) -> dict:
    chunks = [(p.number, p.text) for p in pages if p.number in target.pages]
    user = f"Target table: {target.label} — {target.caption}\n\n{_pages_block(chunks)}"
    data = _call_json(provider, load_prompt("extract_table"), user, cache_key)
    if not isinstance(data.get("columns"), list):
        raise LLMError("Model reply has no 'columns' list.")
    return data
