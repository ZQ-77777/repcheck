"""Generate the PDF fixtures in tests/fixtures/ (developer script, run once).

  tight_spacing.pdf   : normal body text plus a table caption typeset with no word spaces
                        (not generated here, kept as a hand-made fixture)
  rotated_tables.pdf  : three pages with a regression table
                        p.1 table drawn rotated 90° inside a portrait page
                        p.2 ordinary content on a page with /Rotate 90
                        p.3 ordinary upright page (control, must not change)

The point of the fixture is the failure mode: on p.1 and p.2 pdfplumber's default extraction
returns one word per line, often in reverse ("4\\nELBAT"), so no caption line can be matched.

Requires: reportlab.
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures"

BODY = [
    "4. Results",
    "Table 4 reports the cross-sectional determinants of the market reaction to capex forecasts.",
    "The dependent variable is CAR and standard errors are clustered by firm.",
]


def _table(c: canvas.Canvas, x: float, y: float, label: str, title: str) -> None:
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, label)
    c.setFont("Helvetica", 9)
    c.drawString(x, y - 13, title)
    rows = [("CAR", "0.0123***", "(0.0041)"),
            ("SIZE", "-0.0456**", "(0.0198)"),
            ("LEV", "0.1120*", "(0.0581)"),
            ("Observations", "11,250", "")]
    for i, (name, coef, se) in enumerate(rows):
        top = y - 30 - i * 12
        c.drawString(x, top, name)
        c.drawString(x + 95, top, coef)
        c.drawString(x + 165, top, se)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(x, y - 100, "Notes: This table reports OLS estimates. *** p<0.01, ** p<0.05, * p<0.1.")


def _body(c: canvas.Canvas, x: float, y: float) -> None:
    c.setFont("Helvetica", 10)
    for i, line in enumerate(BODY):
        c.drawString(x, y - i * 14, line)


def build() -> Path:
    path = OUT / "rotated_tables.pdf"
    OUT.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)

    # p.1: the table block is rotated 90° counter-clockwise inside a portrait page, the usual
    # way a journal prints a wide table so that the reader turns the paper. The page also carries
    # an upright publisher banner and a 270° download sidebar, as RFS PDFs do; before the fix the
    # banner was projected onto the table's axes and split the caption ("TABLE 4" + banner letters).
    c.saveState()
    c.translate(A4[0], 0)
    c.rotate(90)
    _body(c, 60, 520)
    _table(c, 60, 380, "TABLE 4", "Determinants of the Market Reaction to Capex Forecasts")
    c.restoreState()
    c.setFont("Courier", 6)
    c.drawString(40, 810, "[20:08 2/7/2020 RFS-OP-REVF190138.tex] Page: 3870 3854-3888")
    c.saveState()
    c.translate(560, 60)
    c.rotate(-90)
    c.setFont("Helvetica", 6)
    c.drawString(0, 0, "Downloaded from academic.oup.com/rfs/article/33/8/3854 by a university user")
    c.restoreState()
    c.showPage()

    # p.2: same visual result, but produced with the /Rotate page attribute instead.
    c.setPageRotation(90)
    _body(c, 60, 520)
    _table(c, 60, 380, "TABLE 5", "Determinants of the Market Reaction to Capex Forecasts")
    c.showPage()

    # p.3: control page, ordinary upright text and caption.
    c.setPageRotation(0)
    _body(c, 60, 780)
    _table(c, 60, 640, "TABLE 6", "Determinants of the Market Reaction to Capex Forecasts")
    c.showPage()
    c.save()
    return path


if __name__ == "__main__":
    print("written:", build())
