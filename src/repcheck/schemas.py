"""Shared data structures. This module is the ONLY interface between modules.

Team rule: change a field here only after telling the integrator, and update the
affected tests in the same pull request.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional, Union

Value = Union[str, list, None]   # a string, a list of strings, or None


class ExtractionStatus(str, Enum):
    VERIFIED = "verified"        # every evidence quote was found in the PDF text
    UNVERIFIED = "unverified"    # a value was given, but a quote could not be matched
    MISSING = "missing"          # the model reported the field as not found


class ReviewStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EDITED = "edited"
    REJECTED = "rejected"
    NOT_IN_PAPER = "not_in_paper"


@dataclass
class Page:
    number: int   # 1-based PDF page index (printed page numbers are unreliable)
    text: str     # cleaned text, line breaks preserved


@dataclass
class TableTarget:
    label: str            # canonical label, e.g. "Table 3"
    number: int
    pages: list
    caption: str
    notes: str


@dataclass
class Context:
    target: TableTarget
    chunks: list                 # list of (page number, page text), sorted by page
    keyword_hits: dict           # checklist key -> list of pages with keyword matches


@dataclass
class Evidence:
    page: int
    quote: str
    verified: bool = False
    page_corrected: bool = False   # True if the quote was found on a different page


@dataclass
class ChecklistItem:
    key: str
    label: str
    required: bool
    extraction_status: ExtractionStatus
    value: Value = None
    evidence: list = field(default_factory=list)   # list[Evidence]
    hint: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.PENDING
    user_value: Value = None
    user_note: Optional[str] = None

    def final_value(self) -> Value:
        """Value that downstream exports may use (only after human review)."""
        if self.review_status == ReviewStatus.EDITED:
            return self.user_value
        if self.review_status == ReviewStatus.CONFIRMED:
            return self.value
        return None


@dataclass
class Checklist:
    source_file: str
    content_hash: str
    table: TableTarget
    template: str
    model_name: str
    items: list                  # list[ChecklistItem]
    paper_title: Optional[str] = None

    def get(self, key: str) -> Optional[ChecklistItem]:
        return next((i for i in self.items if i.key == key), None)

    def ready_to_export(self) -> bool:
        return all(i.review_status != ReviewStatus.PENDING for i in self.items if i.required)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Checklist":
        items = [
            ChecklistItem(
                key=i["key"], label=i["label"], required=i["required"],
                extraction_status=ExtractionStatus(i["extraction_status"]),
                value=i.get("value"),
                evidence=[Evidence(**e) for e in i.get("evidence", [])],
                hint=i.get("hint"),
                review_status=ReviewStatus(i.get("review_status", "pending")),
                user_value=i.get("user_value"), user_note=i.get("user_note"),
            )
            for i in d["items"]
        ]
        return cls(
            source_file=d["source_file"], content_hash=d["content_hash"],
            table=TableTarget(**d["table"]), template=d["template"],
            model_name=d["model_name"], items=items, paper_title=d.get("paper_title"),
        )


# ------------------------------------------------------------------ stage 2: result check

@dataclass
class TableCell:
    variable: str
    coef_raw: str
    paren_raw: Optional[str]
    coef: Optional[float]
    paren: Optional[float]        # standard error or t-statistic (see TableColumn.paren_kind)
    stars: int
    verified: bool                # numbers found verbatim on the table page(s)


@dataclass
class TableColumn:
    label: str                    # "(1)", "(2)", ...
    dependent_var: Optional[str]
    paren_kind: str               # "se", "t" or "none"
    n_raw: Optional[str]
    n: Optional[int]
    n_verified: bool
    cells: list                   # list[TableCell]


@dataclass
class PaperTable:
    label: str
    model_name: str
    columns: list                 # list[TableColumn]

    def unverified_numbers(self) -> list:
        out = []
        for c in self.columns:
            if c.n_raw and not c.n_verified:
                out.append(f"{c.label} N={c.n_raw}")
            out += [f"{c.label} {x.variable}={x.coef_raw}" for x in c.cells if not x.verified]
        return out


@dataclass
class ResultRow:
    column: str
    variable: str
    coef: float
    se: Optional[float] = None
    pvalue: Optional[float] = None
    n: Optional[int] = None


@dataclass
class Discrepancy:
    column: str
    variable: Optional[str]
    kind: str          # n_mismatch | column_missing | variable_missing | sign_flip | scale | cross_column_scale | magnitude | significance | se_mismatch
    severity: str      # major | minor
    paper: Optional[str]
    replicated: Optional[str]
    message: str
    suspects: list = field(default_factory=list)        # checklist keys to re-check
    suspect_notes: list = field(default_factory=list)   # readable notes with page evidence


@dataclass
class ComparisonReport:
    table_label: str
    total_cells: int
    matched_cells: int
    discrepancies: list           # list[Discrepancy]
    unverified_paper_numbers: list

    @property
    def overall(self) -> str:
        if any(d.severity == "major" for d in self.discrepancies):
            return "major differences"
        if self.discrepancies:
            return "minor differences"
        return "match"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["overall"] = self.overall
        return d
