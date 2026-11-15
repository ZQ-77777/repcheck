"""Orchestration: the only module that calls the others in order.

run_spec   : PDF + table label            -> Checklist (all items pending review)
run_table  : PDF + table label            -> PaperTable (verified numbers)
run_compare: PDF + table label + results  -> ComparisonReport
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .checklist_templates import get_template
from .comparator import compare, load_results_csv
from .extractor import extract_spec, extract_table_numbers, make_cache_key
from .llm.base import LLMProvider
from .pdf_parser import file_hash, guess_title, parse_pdf
from .retriever import DEFAULT_MAX_PAGES, build_context
from .schemas import Checklist, ComparisonReport, PaperTable
from .table_locator import locate_table
from .table_numbers import build_paper_table
from .verifier import build_checklist


@dataclass
class LoadedPaper:
    path: Path
    pages: list
    content_hash: str
    title: str | None


def load_paper(pdf_path: str | Path) -> LoadedPaper:
    pages = parse_pdf(pdf_path)
    return LoadedPaper(Path(pdf_path), pages, file_hash(pdf_path), guess_title(pages))


def run_spec(paper: LoadedPaper, table_label: str, provider: LLMProvider,
             template: str = "regression", max_pages: int = DEFAULT_MAX_PAGES) -> Checklist:
    fields = get_template(template)
    target = locate_table(paper.pages, table_label)
    context = build_context(paper.pages, target, fields, max_pages)
    raw = extract_spec(context, fields, provider, make_cache_key("spec", paper.content_hash, target, template))
    return build_checklist(raw, paper.pages, context, fields, source_file=paper.path.name,
                           content_hash=paper.content_hash, template=template,
                           model_name=provider.name, paper_title=paper.title)


def run_table(paper: LoadedPaper, table_label: str, provider: LLMProvider) -> PaperTable:
    target = locate_table(paper.pages, table_label)
    raw = extract_table_numbers(target, paper.pages, provider,
                                make_cache_key("table", paper.content_hash, target))
    return build_paper_table(raw, target, paper.pages, provider.name)


def run_compare(paper: LoadedPaper, table_label: str, results_source, provider: LLMProvider,
                checklist: Checklist | None = None) -> tuple[PaperTable, ComparisonReport]:
    results = load_results_csv(results_source)          # fail fast on a bad CSV, before any API call
    table = run_table(paper, table_label, provider)
    return table, compare(table, results, checklist)
