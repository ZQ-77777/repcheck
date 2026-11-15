# Replication checklist — Table 2

- Paper: Board Independence and Dividend Payouts
- Table: TABLE II: Board Independence and Dividend Payout (PDF page 3)
- Model: mock: hand-written fixture — replace by a real live-mode run · template: regression · exported 2026-11-16 03:13
- Review complete: NO — pending items remain

| Field | Extracted value | Evidence | Check | Review | Final value |
|---|---|---|---|---|---|
| Sample period * | 2005-2018 | p.2: “Our sample spans 2005 to 2018.” | ✅ verified | pending | — |
| Data sources * | • Compustat (accounting data)<br>• BoardEx (board composition) | p.2: “Accounting data come from Compustat and board composition data come from BoardEx.” | ✅ verified | pending | — |
| Sample filters * | • Require non-missing board data<br>• Require positive total assets | p.2: “We require firms to have non-missing board data and positive total assets.” | ✅ verified | pending | — |
| Unit of observation * | firm-year | p.2: “Each observation is a firm-year, and the final sample has 9,876 firm-years.” | ✅ verified | pending | — |
| Dependent variable * | PAYOUT: Common dividends (DVC) divided by income before extraordinary items (IB) | p.4: “PAYOUT Common dividends (DVC) divided by income before extraordinary items (IB).” | ✅ verified | pending | — |
| Key independent variable(s) * | • BOARD_IND: Fraction of directors classified as independent in BoardEx | p.4: “BOARD_IND Fraction of directors classified as independent in BoardEx.” | ✅ verified | pending | — |
| Control variables * | • SIZE: Natural log of total assets (AT)<br>• ROA: Income before extraordinary items (IB) divided by total assets (AT)<br>• LEV: Total debt (DLTT + DLC) divided by total assets (AT) (column 2 only) | p.4: “SIZE Natural log of total assets (AT).”<br>p.4: “LEV Total debt (DLTT + DLC) divided by total assets (AT).” | ✅ verified | pending | — |
| Fixed effects * | Industry and year fixed effects | p.2: “All regressions include industry and year fixed effects” | ✅ verified | pending | — |
| Standard errors * | — | — | ❌ missing<br>*Not found, and no related keywords in the paper. Papers usually report this in the table notes or the research design section. It may be genuinely unreported: mark 'Not in paper' and note it.* | pending | — |
| Estimation method * | OLS | p.2: “We estimate OLS regressions of PAYOUT on BOARD_IND and firm characteristics.” | ✅ verified | pending | — |
| Subsamples / column structure | Same sample in both columns; column 2 adds LEV as an additional control | p.2: “TABLE II reports the estimates with and without leverage as an additional control.” | ✅ verified | pending | — |
| Winsorization / outliers | — | — | ❌ missing<br>*Not found, and no related keywords in the paper. Papers usually report this in the Data/Sample section or the appendix. It may be genuinely unreported: mark 'Not in paper' and note it.* | pending | — |
| Reported sample size | 9,876 firm-years | p.2: “the final sample has 9,876 firm-years” | ✅ verified | pending | — |

\* required field
