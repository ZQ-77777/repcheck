"""Generate the example inputs in examples/inputs/ (developer script, run once).

  e1_coverage_investment.pdf : synthetic paper, Table 3, information spread over body/notes/appendix
  e2_board_payout.pdf        : synthetic paper, TABLE II (roman numeral), t-statistics,
                               winsorization and standard-error method deliberately NOT reported
  f1_scanned.pdf             : image-only copy of e2 (failure case: no text layer)

Both papers are FICTIONAL and created only to test this tool; all numbers are made up.
Requires: reportlab, pdfplumber (for rasterising), Pillow.
"""
from pathlib import Path

import pdfplumber
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parents[1] / "examples" / "inputs"
ss = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=ss["Normal"], fontSize=10.5, leading=14, spaceAfter=8)
NOTE = ParagraphStyle("note", parent=BODY, fontSize=9, leading=12)
H1 = ParagraphStyle("h1", parent=ss["Heading2"], fontSize=13)
TITLE = ParagraphStyle("title", parent=ss["Title"], fontSize=17)
BANNER = ParagraphStyle("banner", parent=BODY, fontSize=8, textColor=colors.grey)
BANNER_TEXT = ("SYNTHETIC TEST DOCUMENT. Fictional paper created for MSDM5051 Project 2 testing; "
               "not a real study, all numbers are invented.")


def P(text, style=BODY):
    return Paragraph(text, style)


def grid(rows, widths):
    t = Table(rows, colWidths=widths)
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5), ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black), ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
    return t


def build(path, story):
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2.3 * cm, rightMargin=2.3 * cm,
                      topMargin=2 * cm, bottomMargin=2 * cm, title=path.stem,
                      invariant=1).build(story)


def paper_e1():
    s = [P(BANNER_TEXT, BANNER),
         P("Analyst Coverage and Corporate Investment", TITLE),
         P("Alex Example and Blair Sample", ss["Normal"]), Spacer(1, 10),
         P("<b>Abstract.</b> We study whether firms followed by more sell-side analysts invest more. "
           "Using a panel of U.S. public firms, we find that analyst coverage is positively associated "
           "with next-year capital expenditures, consistent with coverage reducing financing frictions."),
         P("1. Introduction", H1),
         P("Analysts produce information that lowers the cost of external capital. If this channel matters, "
           "firms with more analyst coverage should invest more, holding investment opportunities fixed. "
           "Our main evidence is presented in Table 3, which reports regressions of investment on coverage "
           "with progressively richer sets of controls."),
         P("The rest of the paper is organized as follows. Section 2 describes the data and the sample. "
           "Section 3 explains the research design. Section 4 presents the results, and the Appendix "
           "defines all variables."),
         PageBreak(),
         P("2. Data and Sample", H1),
         P("Our sample covers fiscal years 2003 to 2019. We obtain financial statement data from Compustat, "
           "stock price data from CRSP, and analyst coverage from I/B/E/S."),
         P("We apply the following screens. We exclude financial firms (SIC codes 6000-6999) and utilities "
           "(SIC codes 4900-4999) because their investment is subject to regulation. We require non-missing "
           "values for all regression variables and lagged total assets of at least $10 million."),
         P("The unit of observation is the firm-year. The final sample consists of 24,318 firm-year "
           "observations from 3,207 unique firms. To mitigate the influence of outliers, all continuous "
           "variables are winsorized at the 1st and 99th percentiles of their annual distributions."),
         P("Table 2 reports descriptive statistics. The average firm invests about 5.6 percent of its lagged "
           "assets and is followed by roughly seven analysts."),
         P("Table 2", ss["Heading4"]), P("Descriptive Statistics", ss["Normal"]),
         grid([["Variable", "Mean", "Std. Dev.", "P25", "Median", "P75"],
               ["INVEST", "0.056", "0.061", "0.018", "0.037", "0.071"],
               ["COVERAGE", "1.812", "0.904", "1.099", "1.946", "2.485"],
               ["SIZE", "6.725", "1.981", "5.274", "6.640", "8.051"],
               ["LEV", "0.231", "0.198", "0.054", "0.205", "0.352"]],
              [3 * cm] + [2.2 * cm] * 5),
         P("This table reports descriptive statistics for the 24,318 firm-year observations.", NOTE),
         PageBreak(),
         P("3. Research Design", H1),
         P("We estimate the following model: INVEST(i,t+1) = b0 + b1 COVERAGE(i,t) + Controls(i,t) + "
           "firm fixed effects + year fixed effects + e(i,t+1). The dependent variable INVEST is next-year "
           "capital expenditures scaled by lagged total assets. The variable of interest is COVERAGE."),
         P("We estimate all models using ordinary least squares (OLS). Firm fixed effects absorb time-invariant "
           "differences in investment policy, and year fixed effects absorb aggregate shocks. Standard errors "
           "are clustered at the firm level."),
         P("4. Results", H1),
         P("Table 3 presents the main results. Column (1) includes only COVERAGE. Column (2) adds SIZE, LEV "
           "and MTB, and column (3) further adds CASH and ROA. Across all specifications, the coefficient on "
           "COVERAGE is positive and significant at the 1% level. In column (3), a one-standard-deviation "
           "increase in COVERAGE is associated with an increase in INVEST of about 0.013, roughly 23 percent "
           "of the sample mean."),
         PageBreak(),
         P("Table 3", ss["Heading4"]),
         P("Analyst Coverage and Corporate Investment", ss["Normal"]), Spacer(1, 6),
         grid([["Dependent variable: INVEST", "(1)", "(2)", "(3)"],
               ["COVERAGE", "0.0215***", "0.0168***", "0.0142***"], ["", "(0.0042)", "(0.0039)", "(0.0037)"],
               ["SIZE", "", "-0.0031**", "-0.0027*"], ["", "", "(0.0014)", "(0.0015)"],
               ["LEV", "", "-0.0452***", "-0.0398***"], ["", "", "(0.0087)", "(0.0085)"],
               ["MTB", "", "0.0064***", "0.0058***"], ["", "", "(0.0011)", "(0.0011)"],
               ["CASH", "", "", "0.0311**"], ["", "", "", "(0.0129)"],
               ["ROA", "", "", "0.0874***"], ["", "", "", "(0.0196)"],
               ["Firm FE", "Yes", "Yes", "Yes"], ["Year FE", "Yes", "Yes", "Yes"],
               ["Observations", "24,318", "24,318", "24,318"], ["Adjusted R2", "0.412", "0.428", "0.436"]],
              [5.2 * cm, 3 * cm, 3 * cm, 3 * cm]),
         Spacer(1, 6),
         P("This table reports OLS regressions of next-year investment on analyst coverage. Variables are "
           "defined in Appendix A. Standard errors clustered by firm are reported in parentheses. ***, **, "
           "and * denote significance at the 1%, 5%, and 10% levels, respectively.", NOTE),
         PageBreak(),
         P("Appendix A. Variable Definitions", H1),
         grid([["Variable", "Definition"],
               ["INVEST", "Capital expenditures (CAPX) in year t+1 divided by total assets (AT) in year t."],
               ["COVERAGE", "Natural log of one plus the number of analysts with an annual EPS forecast (I/B/E/S)."],
               ["SIZE", "Natural log of total assets (AT)."],
               ["LEV", "Long-term debt plus debt in current liabilities (DLTT + DLC) divided by AT."],
               ["MTB", "Market value of equity (PRCC_F x CSHO) divided by book equity (CEQ)."],
               ["CASH", "Cash and short-term investments (CHE) divided by AT."],
               ["ROA", "Income before extraordinary items (IB) divided by AT."]],
              [2.6 * cm, 13.4 * cm])]
    build(OUT / "e1_coverage_investment.pdf", s)


def paper_e2():
    s = [P(BANNER_TEXT, BANNER),
         P("Board Independence and Dividend Payouts", TITLE),
         P("Casey Placeholder", ss["Normal"]), Spacer(1, 10),
         P("<b>Abstract.</b> We examine whether more independent boards pay out more cash to shareholders. "
           "Firms with a higher share of independent directors have higher dividend payout ratios, "
           "consistent with independent boards limiting the free cash flow available to managers."),
         P("1. Introduction", H1),
         P("Agency theory predicts that monitoring by independent directors forces managers to disgorge "
           "excess cash. We test this prediction for U.S. firms and report the main estimates in TABLE II. "
           "The effect is economically meaningful and survives controls for size and profitability."),
         PageBreak(),
         P("2. Data and Research Design", H1),
         P("Our sample spans 2005 to 2018. Accounting data come from Compustat and board composition data "
           "come from BoardEx. We require firms to have non-missing board data and positive total assets. "
           "Each observation is a firm-year, and the final sample has 9,876 firm-years."),
         P("We estimate OLS regressions of PAYOUT on BOARD_IND and firm characteristics. All regressions "
           "include industry and year fixed effects, so the estimates compare firms within the same "
           "industry and year."),
         P("Results are discussed in Section 3. TABLE II reports the estimates with and without leverage as "
           "an additional control."),
         P("3. Results", H1),
         P("The coefficient on BOARD_IND is positive and statistically significant in both columns. Moving "
           "from the 25th to the 75th percentile of board independence raises the payout ratio by about "
           "two percentage points."),
         PageBreak(),
         P("TABLE II: Board Independence and Dividend Payout", ss["Heading4"]), Spacer(1, 6),
         grid([["Dependent variable: PAYOUT", "(1)", "(2)"],
               ["BOARD_IND", "0.0842***", "0.0617**"], ["", "(3.12)", "(2.34)"],
               ["SIZE", "0.0105**", "0.0098**"], ["", "(2.21)", "(2.05)"],
               ["ROA", "0.2290***", "0.2154***"], ["", "(4.05)", "(3.87)"],
               ["LEV", "", "-0.0731**"], ["", "", "(-2.18)"],
               ["Industry FE", "Yes", "Yes"], ["Year FE", "Yes", "Yes"],
               ["Observations", "9,876", "9,876"], ["R-squared", "0.187", "0.192"]],
              [6 * cm, 3.5 * cm, 3.5 * cm]),
         Spacer(1, 6),
         P("Notes: This table reports OLS estimates of the payout regression. t-statistics are reported in "
           "parentheses. ***, **, * indicate p&lt;0.01, p&lt;0.05 and p&lt;0.1.", NOTE),
         PageBreak(),
         P("Appendix: Variable Definitions", H1),
         grid([["Variable", "Definition"],
               ["PAYOUT", "Common dividends (DVC) divided by income before extraordinary items (IB)."],
               ["BOARD_IND", "Fraction of directors classified as independent in BoardEx."],
               ["SIZE", "Natural log of total assets (AT)."],
               ["ROA", "Income before extraordinary items (IB) divided by total assets (AT)."],
               ["LEV", "Total debt (DLTT + DLC) divided by total assets (AT)."]],
              [2.8 * cm, 13.2 * cm])]
    build(OUT / "e2_board_payout.pdf", s)


def scanned_copy(src, dst):
    with pdfplumber.open(str(src)) as pdf:
        images = [p.to_image(resolution=80).original.convert("RGB") for p in pdf.pages]
    images[0].save(dst, save_all=True, append_images=images[1:])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    paper_e1()
    paper_e2()
    scanned_copy(OUT / "e2_board_payout.pdf", OUT / "f1_scanned.pdf")
    print("written:", *sorted(p.name for p in OUT.glob("*.pdf")))
