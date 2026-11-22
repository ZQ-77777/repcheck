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


def quote_context(page_text: str, quote: str, width: int = 200) -> str | None:
    """A ~`width`-character window of `page_text` around the first match of `quote`,
    with the matched span wrapped in [[ ]]. Matching uses the same normalization as
    the verifier (hyphen joins, lost word spaces, curly quotes), so the UI shows the
    same span the check accepted. None if the quote cannot be located on the page."""
    n = normalize_for_match(quote)
    if not n:
        return None
    cleaned, norm, idx = _norm_with_index(page_text)
    start_i = end_i = None
    pos = norm.find(n)
    if pos >= 0:
        start_i, end_i = idx[pos], idx[pos + len(n) - 1]
    else:
        # same fallback as partial_ratio: text whose word spaces were lost
        n_c = re.sub(r"\s+", "", n)
        if len(n_c) < 15:
            return None
        compact = [(c, i) for c, i in zip(norm, idx) if c != " "]
        p = "".join(c for c, _ in compact).find(n_c)
        if p < 0:
            return None
        start_i, end_i = compact[p][1], compact[p + len(n_c) - 1][1]
    lo = max(0, start_i - width // 2)
    hi = min(len(cleaned), end_i + 1 + width // 2)
    return f"{cleaned[lo:start_i]}[[{cleaned[start_i:end_i + 1]}]]{cleaned[end_i + 1:hi]}"


def _norm_with_index(text: str) -> tuple[str, str, list[int]]:
    """clean_text(text), its normalize_for_match form, and for each normalized char the
    index of the cleaned char it came from (-1 for chars dropped by normalization)."""
    cleaned = clean_text(text)
    pairs = [(c, i) for i, c in enumerate(cleaned)]
    # join words hyphenated at line ends (same rule as normalize_for_match)
    joined, i = [], 0
    while i < len(pairs):
        c, idx = pairs[i]
        if (c == "-" and i + 1 < len(pairs) and pairs[i + 1][0] == "\n"
                and i > 0 and (pairs[i - 1][0].isalnum() or pairs[i - 1][0] == "_")
                and i + 2 < len(pairs) and (pairs[i + 2][0].isalnum() or pairs[i + 2][0] == "_")):
            i += 2
            continue
        joined.append((c, idx))
        i += 1
    # collapse whitespace runs to a single space (first char of the run is kept)
    res, prev_ws = [], False
    for c, idx in joined:
        ws = c in " \t\n\r\f\v"
        if ws:
            if prev_ws:
                continue
            c, prev_ws = " ", True
        else:
            prev_ws = False
        res.append((c, idx))
    return cleaned, "".join(c for c, _ in res).lower(), [idx for _, idx in res]


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
