"""M5 — RepCheck web app.   Run:  streamlit run app.py

Tab 1  Spec checklist : upload a paper, pick a table, review each extracted item, export.
Tab 2  Result check   : upload replication results (CSV) and get a discrepancy report.
All logic lives in src/repcheck; this file only handles layout and session state.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from repcheck.checklist_templates import get_template                         # noqa: E402
from repcheck.comparator import ResultsFormatError                            # noqa: E402
from repcheck.exporter import (checklist_to_json, checklist_to_markdown,      # noqa: E402
                               render_skeleton, report_to_markdown)
from repcheck.llm import LLMError, get_provider                               # noqa: E402
from repcheck.llm.factory import default_mode                                 # noqa: E402
from repcheck.pdf_parser import InvalidPDFError, ScannedPDFError, file_hash   # noqa: E402
from repcheck.pipeline import load_paper, run_compare, run_spec               # noqa: E402
from repcheck.review import apply_review, parse_user_value, progress          # noqa: E402
from repcheck.schemas import ExtractionStatus, ReviewStatus                   # noqa: E402
from repcheck.table_locator import TableNotFoundError, list_tables            # noqa: E402

USER_ERRORS = (InvalidPDFError, ScannedPDFError, TableNotFoundError, LLMError, ResultsFormatError, ValueError)
INPUTS = ROOT / "examples" / "inputs"
EXAMPLES = {  # label -> (pdf, default table, results csv)
    "Example 1 — analyst coverage (Table 3)": ("e1_coverage_investment.pdf", "Table 3", "e1_replication_results.csv"),
    "Example 2 — board independence (TABLE II)": ("e2_board_payout.pdf", "Table 2", "e2_replication_results.csv"),
}
# Real-paper case study (not distributed): shown only when the PDF is present on this computer.
if (INPUTS.parent / "private" / "jw2020.pdf").exists():
    EXAMPLES["Jayaraman & Wu (2020) — Table 3"] = ("../private/jw2020.pdf", "Table 3", "jw2020_table3_results.csv")
STATUS_BADGE = {ExtractionStatus.VERIFIED: "✅ verified", ExtractionStatus.UNVERIFIED: "⚠️ check quote",
                ExtractionStatus.MISSING: "❌ not found"}
ACTION_LABEL = {ReviewStatus.PENDING: "Pending", ReviewStatus.CONFIRMED: "Confirm",
                ReviewStatus.EDITED: "Edit", ReviewStatus.REJECTED: "Reject",
                ReviewStatus.NOT_IN_PAPER: "Not in paper"}

st.set_page_config(page_title="RepCheck", page_icon="🔎", layout="wide")

# On Streamlit Community Cloud the API settings come from the app's Secrets, not from .env.
try:
    for _key in ("API_KEY", "BASE_URL", "MODEL", "LLM_PROVIDER"):
        if _key in st.secrets and not os.getenv(_key):
            os.environ[_key] = str(st.secrets[_key])
except Exception:  # no secrets configured (normal when running locally)
    pass
state = st.session_state


def show_error(exc: Exception) -> None:
    st.error(f"{type(exc).__name__}: {exc}")


# ------------------------------------------------------------------------------ sidebar
with st.sidebar:
    st.title("🔎 RepCheck")
    st.caption("Evidence-grounded replication specs and result checks")
    modes = ["mock", "live"]
    mode = st.radio("Model", modes, index=modes.index(default_mode()) if default_mode() in modes else 0,
                    help="mock replays saved answers for the example papers (no API key). "
                         "live calls the API set in .env and caches every answer.")
    source = st.selectbox("Paper", ["Upload a PDF", *EXAMPLES])
    uploaded = st.file_uploader("Paper PDF", type=["pdf"]) if source == "Upload a PDF" else None
    st.divider()
    st.caption("Human review is required before any code is exported. Quotes are checked against "
               "the PDF text; numbers are checked against the table page.")


def current_pdf() -> Path | None:
    if source in EXAMPLES:
        return INPUTS / EXAMPLES[source][0]
    if uploaded is None:
        return None
    tmp = Path(tempfile.gettempdir()) / "repcheck_uploads"
    tmp.mkdir(exist_ok=True)
    path = tmp / Path(uploaded.name).name
    path.write_bytes(uploaded.getvalue())
    return path


pdf_path = current_pdf()
if pdf_path is None:
    st.info("Choose an example paper or upload a text-based PDF in the sidebar to start.")
    st.stop()

pdf_id = file_hash(pdf_path)
if state.get("pdf_id") != pdf_id:                   # new paper -> reset everything
    for k in ("paper", "checklist", "report", "paper_table", "pdf_id"):
        state.pop(k, None)
    try:
        state.paper = load_paper(pdf_path)
    except USER_ERRORS as exc:
        show_error(exc)
        st.stop()
    state.pdf_id, state.pdf_path = pdf_id, str(pdf_path)

paper = state.paper
tables = list_tables(paper.pages)
st.subheader(paper.title or pdf_path.name)
st.caption(f"{pdf_path.name} · {len(paper.pages)} pages · tables found: {', '.join(tables) or 'none'}")
default_table = EXAMPLES[source][1] if source in EXAMPLES else (tables[-1] if tables else "Table 1")
table_label = st.text_input("Table to replicate", value=default_table, help='e.g. "Table 3", "3" or "III"')

tab_spec, tab_check = st.tabs(["1 · Spec checklist", "2 · Result check"])

# ------------------------------------------------------------------------- tab 1: spec
with tab_spec:
    if st.button("Extract checklist", type="primary"):
        try:
            with st.spinner("Locating the table, selecting pages and asking the model…"):
                state.checklist = run_spec(paper, table_label, get_provider(mode))
        except USER_ERRORS as exc:
            show_error(exc)

    checklist = state.get("checklist")
    if checklist is not None:
        t = checklist.table
        st.markdown(f"**{t.caption}** — PDF page {', '.join(map(str, t.pages))} · model: `{checklist.model_name}`")
        done, total = progress(checklist)
        st.progress(done / total if total else 1.0, text=f"Required items reviewed: {done}/{total}")
        fields = {f.key: f for f in get_template(checklist.template)}

        for item in checklist.items:
            spec = fields[item.key]
            title = f"{STATUS_BADGE[item.extraction_status]} · {item.label}{' *' if item.required else ''}" \
                    f" — {ACTION_LABEL[item.review_status]}"
            # keep an item open while it is being edited (its title changes, which would collapse it)
            with st.expander(title, expanded=item.review_status == ReviewStatus.PENDING
                             or state.get("open_item") == item.key):
                if item.value is not None:
                    st.markdown("\n".join(f"- {v}" for v in item.value) if isinstance(item.value, list)
                                else item.value)
                for e in item.evidence:
                    mark = "✅" if e.verified else "⚠️ not found in PDF"
                    moved = " (page corrected)" if e.page_corrected else ""
                    st.caption(f"{mark} p.{e.page}{moved}: “{e.quote}”")
                if item.hint:
                    st.info(item.hint)

                options = list(ReviewStatus)
                if item.value is None:
                    options.remove(ReviewStatus.CONFIRMED)
                key = f"{checklist.content_hash}_{item.key}"
                action = st.radio("Decision", options, key=f"act_{key}", horizontal=True,
                                  index=options.index(item.review_status),
                                  format_func=lambda s: ACTION_LABEL[s])
                user_value = None
                if action == ReviewStatus.EDITED:
                    start = item.user_value or item.value or ""
                    start = "\n".join(start) if isinstance(start, list) else start
                    text = st.text_area("Correct value" + (" (one per line)" if spec.is_list else ""),
                                        value=start, key=f"val_{key}")
                    user_value = parse_user_value(text, spec.is_list)
                note = st.text_input("Note (optional)", value=item.user_note or "", key=f"note_{key}")
                if action != item.review_status or user_value != item.user_value or \
                        (note or None) != item.user_note:
                    try:
                        apply_review(checklist, item.key, action, user_value, note)
                        state.open_item = item.key if action == ReviewStatus.EDITED else None
                        st.rerun()
                    except ValueError as exc:
                        st.warning(str(exc))

        st.divider()
        stem = Path(checklist.source_file).stem
        c1, c2, c3 = st.columns(3)
        c1.download_button("Checklist (.md)", checklist_to_markdown(checklist), f"{stem}_checklist.md")
        c2.download_button("Checklist (.json)", checklist_to_json(checklist), f"{stem}_checklist.json")
        ready = checklist.ready_to_export()
        c3.download_button("Code skeleton (.py)", render_skeleton(checklist) if ready else "",
                           f"{stem}_skeleton.py", disabled=not ready,
                           help=None if ready else "Review all required items first.")
        if ready:
            with st.expander("Preview code skeleton"):
                st.code(render_skeleton(checklist), language="python")

# ------------------------------------------------------------------- tab 2: result check
with tab_check:
    st.markdown("Upload your replication results as CSV with columns "
                "`column, variable, coef` and optionally `se, pvalue, n` (one row per coefficient).")
    if source in EXAMPLES:
        example_csv = INPUTS / EXAMPLES[source][2]
        results_bytes = example_csv.read_bytes() if example_csv.exists() else None
        st.caption(f"Using example results: {example_csv.name}" if results_bytes
                   else f"Example results not found: put them in examples/inputs/{example_csv.name}")
    else:
        up = st.file_uploader("Results CSV", type=["csv"])
        results_bytes = up.getvalue() if up else None
    if state.get("checklist") is None:
        st.caption("Tip: extract and review the checklist first — the report then points to the "
                   "exact page evidence for each likely cause.")
    if st.button("Check results", type="primary", disabled=results_bytes is None):
        try:
            with st.spinner("Reading the table numbers and comparing…"):
                state.paper_table, state.report = run_compare(paper, table_label, results_bytes,
                                                              get_provider(mode), state.get("checklist"))
        except USER_ERRORS as exc:
            show_error(exc)

    report = state.get("report")
    if report is not None:
        m1, m2, m3 = st.columns(3)
        m1.metric("Overall", report.overall)
        m2.metric("Coefficients matching", f"{report.matched_cells}/{report.total_cells}")
        m3.metric("Discrepancies", len(report.discrepancies))
        if report.unverified_paper_numbers:
            st.warning("Paper numbers not found on the table page (possible transcription error): "
                       + ", ".join(report.unverified_paper_numbers))
        if report.discrepancies:
            st.dataframe([{"Column": d.column, "Variable": d.variable or "—", "Type": d.kind,
                           "Severity": d.severity, "Paper": d.paper, "Replication": d.replicated,
                           "Message": d.message} for d in report.discrepancies])
        md = report_to_markdown(report)
        if "## Where to look first" in md:
            st.markdown("#### Where to look first")
            st.markdown(md.split("## Where to look first", 1)[1])
        st.download_button("Report (.md)", md, f"{Path(state.pdf_path).stem}_comparison.md")
