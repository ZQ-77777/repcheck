"""RepCheck command-line interface (testing, batch runs, demo fallback).

  python cli.py doctor   [--ping]          check the setup (and the API key with --ping)
  python cli.py tables   PAPER.pdf
  python cli.py spec     PAPER.pdf --table "Table 3" [--mode mock|live] [--out DIR]
  python cli.py skeleton REVIEWED_CHECKLIST.json [--out DIR]
  python cli.py compare  PAPER.pdf --table "Table 3" --results RESULTS.csv [--checklist CHECKLIST.json]

`spec` writes an UNREVIEWED checklist (all items pending). Review happens in the web app
(streamlit run app.py) or by editing review_status in the JSON, then run `skeleton`.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


def _utf8_console() -> None:
    """Chinese-locale Windows consoles use GBK and cannot print symbols such as ✅."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


_utf8_console()

from repcheck.comparator import ResultsFormatError                     # noqa: E402
from repcheck.exporter import (checklist_to_json, checklist_to_markdown,  # noqa: E402
                               render_skeleton, report_to_markdown)
from repcheck.llm import LLMError, get_provider                          # noqa: E402
from repcheck.pdf_parser import InvalidPDFError, ScannedPDFError         # noqa: E402
from repcheck.pipeline import load_paper, run_compare, run_spec          # noqa: E402
from repcheck.review import ExportBlockedError                           # noqa: E402
from repcheck.schemas import Checklist                                   # noqa: E402
from repcheck.table_locator import TableNotFoundError, list_tables       # noqa: E402

USER_ERRORS = (InvalidPDFError, ScannedPDFError, TableNotFoundError, LLMError,
               ResultsFormatError, ExportBlockedError, ValueError, FileNotFoundError)


def _out(args, default: str) -> Path:
    out = Path(args.out or default)
    out.mkdir(parents=True, exist_ok=True)
    return out


def cmd_doctor(args):
    from repcheck.llm.factory import DEFAULT_CACHE_DIR, PROJECT_ROOT, default_mode
    from repcheck.llm.openai_compat import OpenAICompatibleProvider
    problems = []
    py_ok = sys.version_info >= (3, 10)
    print(f"Python {platform.python_version()}: {'OK' if py_ok else 'too old, need 3.10+'}")
    if not py_ok:
        problems.append("Python 3.10 or newer is required")
    for mod, required in (("pdfplumber", True), ("jinja2", True), ("streamlit", True),
                          ("dotenv", False), ("rapidfuzz", False)):
        try:
            importlib.import_module(mod)
            print(f"  {mod}: OK")
        except ImportError:
            print(f"  {mod}: MISSING ({'required' if required else 'optional'})")
            if required:
                problems.append(f"install {mod}: pip install -r requirements.txt")
    mode = default_mode()
    cached = sorted(p.name for p in DEFAULT_CACHE_DIR.glob("*.json"))
    print(f".env file: {'found' if (PROJECT_ROOT / '.env').exists() else 'not found (mock mode only)'}")
    print(f"Default model mode: {mode}")
    print(f"Saved answers in examples/cache: {len(cached)} (mock mode can replay these)")
    if os.getenv("API_KEY"):
        key = os.getenv("API_KEY", "")
        print(f"API_KEY: set ({key[:3]}…{key[-2:]}) · BASE_URL: {os.getenv('BASE_URL', '(default)')} · "
              f"MODEL: {os.getenv('MODEL', '(default)')}")
    else:
        print("API_KEY: not set — live mode unavailable")
    if args.ping:
        reply = OpenAICompatibleProvider.from_env().complete("Reply with the single word OK.", "ping")
        print(f"API ping: OK (model replied {reply.strip()[:40]!r})")
    print("\nReady." if not problems else "\nFix these first:\n- " + "\n- ".join(problems))
    if problems:
        raise SystemExit(1)


def cmd_tables(args):
    print("\n".join(list_tables(load_paper(args.pdf).pages)) or "No tables found.")


def cmd_spec(args):
    paper = load_paper(args.pdf)
    checklist = run_spec(paper, args.table, get_provider(args.mode), template=args.template)
    out = _out(args, f"examples/outputs/{Path(args.pdf).stem}")
    (out / "checklist.json").write_text(checklist_to_json(checklist), encoding="utf-8")
    (out / "checklist.md").write_text(checklist_to_markdown(checklist), encoding="utf-8")
    counts = {}
    for i in checklist.items:
        counts[i.extraction_status.value] = counts.get(i.extraction_status.value, 0) + 1
    print(f"{checklist.table.label} on page(s) {checklist.table.pages}: {counts}")
    print(f"Wrote {out / 'checklist.md'} and checklist.json (review pending)")


def cmd_skeleton(args):
    checklist = Checklist.from_dict(json.loads(Path(args.checklist).read_text(encoding="utf-8")))
    out = _out(args, str(Path(args.checklist).parent))
    (out / "skeleton.py").write_text(render_skeleton(checklist), encoding="utf-8")
    print(f"Wrote {out / 'skeleton.py'}")


def cmd_compare(args):
    paper = load_paper(args.pdf)
    checklist = None
    if args.checklist:
        checklist = Checklist.from_dict(json.loads(Path(args.checklist).read_text(encoding="utf-8")))
    _, report = run_compare(paper, args.table, args.results, get_provider(args.mode), checklist)
    out = _out(args, f"examples/outputs/{Path(args.pdf).stem}")
    (out / "comparison.md").write_text(report_to_markdown(report), encoding="utf-8")
    (out / "comparison.json").write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
                                         encoding="utf-8")
    print(f"{report.table_label}: {report.overall} ({report.matched_cells}/{report.total_cells} match, "
          f"{len(report.discrepancies)} discrepancies)")
    print(f"Wrote {out / 'comparison.md'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="repcheck", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("doctor", help="check the installation and API settings")
    p.add_argument("--ping", action="store_true", help="also send one tiny request to the API")
    p.set_defaults(func=cmd_doctor)
    p = sub.add_parser("tables", help="list tables found in a PDF")
    p.add_argument("pdf")
    p.set_defaults(func=cmd_tables)
    for name, func in (("spec", cmd_spec), ("compare", cmd_compare)):
        p = sub.add_parser(name)
        p.add_argument("pdf")
        p.add_argument("--table", required=True, help='e.g. "Table 3", "3" or "III"')
        p.add_argument("--mode", choices=["mock", "live"], default=None,
                       help="default: live if API_KEY is set, else mock")
        p.add_argument("--out")
        p.set_defaults(func=func)
        if name == "spec":
            p.add_argument("--template", default="regression")
        else:
            p.add_argument("--results", required=True, help="replication results CSV")
            p.add_argument("--checklist", help="reviewed checklist JSON (improves suggestions)")
    p = sub.add_parser("skeleton", help="code skeleton from a reviewed checklist JSON")
    p.add_argument("checklist")
    p.add_argument("--out")
    p.set_defaults(func=cmd_skeleton)

    args = ap.parse_args(argv)
    try:
        args.func(args)
    except USER_ERRORS as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
