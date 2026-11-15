"""Text cleaning and fuzzy matching shared by the parser, verifier and table checker.

Every module that compares model output with PDF text MUST use these functions,
otherwise the same quote can match in one place and fail in another.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

try:  # optional speed-up; the pure-Python fallback gives comparable scores
    from rapidfuzz import fuzz as _rf_fuzz
except ImportError:  # pragma: no cover
    _rf_fuzz = None

_CHAR_MAP = {
    "\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff", "\ufb03": "ffi", "\ufb04": "ffl",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00a0": " ",
}
_TRANS = str.maketrans({k: v for k, v in _CHAR_MAP.items() if len(v) == 1})


def clean_text(text: str) -> str:
    """Light cleaning that keeps line breaks (needed to find table captions)."""
    for k, v in _CHAR_MAP.items():
        if len(v) > 1:
            text = text.replace(k, v)
    text = text.translate(_TRANS)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    return "\n".join(lines)


def normalize_for_match(text: str) -> str:
    """Aggressive normalization for comparing a quote with page text."""
    text = clean_text(text)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)    # join words hyphenated at line ends
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def partial_ratio(needle: str, haystack: str) -> float:
    """Best similarity (0-100) between `needle` and any same-length window of `haystack`."""
    n, h = normalize_for_match(needle), normalize_for_match(haystack)
    if not n or not h:
        return 0.0
    if n in h:
        return 100.0
    # Fallback for PDF text whose word spaces were lost: compare with all whitespace removed.
    n_compact, h_compact = re.sub(r"\s+", "", n), re.sub(r"\s+", "", h)
    if len(n_compact) >= 15 and n_compact in h_compact:
        return 100.0
    if _rf_fuzz is not None:
        return float(_rf_fuzz.partial_ratio(n, h))
    best = 0.0
    sm = SequenceMatcher(None, n, h, autojunk=False)
    for a, b, size in sm.get_matching_blocks():
        if size == 0:
            continue
        start = max(0, b - a)
        window = h[start:start + len(n)]
        best = max(best, SequenceMatcher(None, n, window, autojunk=False).ratio() * 100)
        if best >= 99.5:
            break
    return best


_NUM_CORE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def numeric_core(raw: str) -> str | None:
    """'(0.0031)' -> '0.0031', '-0.012***' -> '-0.012', '24,318' -> '24,318'."""
    m = _NUM_CORE.search(clean_text(raw or "").replace(" ", ""))
    return m.group(0) if m else None


def number_in_text(raw: str, text: str) -> bool:
    """True if the printed number appears in `text` as a whole token."""
    core = numeric_core(raw)
    if core is None:
        return False
    t = clean_text(text)
    # a positive number must not match the digits of a negative one ("0.01" vs "-0.01")
    before = r"(?<![\d.])" if core.startswith("-") else r"(?<![\d.\-])"
    if re.search(before + re.escape(core) + r"(?![\d])", t):
        return True
    # tolerate thousands separators being dropped or added by the model
    plain = core.replace(",", "")
    t_plain = re.sub(r"(?<=\d),(?=\d{3})", "", t)
    return re.search(before + re.escape(plain) + r"(?![\d])", t_plain) is not None
