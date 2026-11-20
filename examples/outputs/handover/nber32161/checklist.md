# Replication checklist — Table 2

- Paper: nber32161.pdf
- Table: Table 2. ChatGPT Predictions vs. CFO Survey Results (PDF page 44)
- Model: deepseek/deepseek-v4-flash-0731 · template: regression · exported 2026-11-19 21:03
- Review complete: NO — pending items remain

| Field | Extracted value | Evidence | Check | Review | Final value |
|---|---|---|---|---|---|
| Sample period * | 2006 to 2020 | p.42: “The sample comprises Compustat firms with earnings conference call transcripts and non-missing financial variables from 2006 to 2020.” | ✅ verified | pending | — |
| Data sources * | • Compustat<br>• Duke CFO Survey<br>• Earnings conference call transcripts | p.42: “Compustat firms with earnings conference call transcripts and non-missing financial variables”<br>p.44: “CFO survey conducted by Duke University” | ✅ verified | pending | — |
| Sample filters * | • Compustat firms with earnings conference call transcripts and non-missing financial variables from 2006 to 2020<br>• Merged final sample of conference call data with CFO survey data to obtain 1,338 firm-quarter observations | p.42: “The sample comprises Compustat firms with earnings conference call transcripts and non-missing financial variables from 2006 to 2020.”<br>p.17: “Merging our final sample of conference call data with the CFO survey data yields a sample of 1,338 firm-quarter observations.” | ✅ verified | pending | — |
| Unit of observation * | firm-quarter | p.44: “This table presents coefficients from a firm-quarter level estimation that regresses the Duke CFO Survey-based measure on the ChatGPT predicted measure of corporate capital expenditure in the next 12 months.” | ✅ verified | pending | — |
| Dependent variable * | CFO Survey Investment: expected capital expenditure change for the next year mentioned by corporate executives during the CFO survey conducted by Duke University | p.44: “CFO Survey Investment is the expected capital expenditure change for the next year mentioned by corporate executives during the CFO survey conducted by Duke University.” | ✅ verified | pending | — |
| Key independent variable(s) * | • ChatGPT Investment Score: capital expenditure change predicted by ChatGPT from firms' earnings call transcripts | p.44: “ChatGPT Investment Score measures the capital expenditure change predicted by ChatGPT from firms' earnings call transcripts.” | ✅ verified | pending | — |
| Control variables * | — | — | ❌ missing<br>*Not found by the model. Keywords for this field appear on p.2, p.5, p.6, p.7, p.11, p.15; check them. If the paper does not report it, mark 'Not in paper'.* | pending | — |
| Fixed effects * | IndustryFE, YearQtrFE | p.44: “IndustryFE N Y YearQtrFE N Y” | ✅ verified | pending | — |
| Standard errors * | clustered by industry | p.44: “the t-statistics, in parentheses, are based on standard errors clustered by industry.” | ✅ verified | pending | — |
| Estimation method * | — | — | ❌ missing<br>*Not found by the model. Keywords for this field appear on p.3, p.9, p.17, p.18, p.19, p.20; check them. If the paper does not report it, mark 'Not in paper'.* | pending | — |
| Subsamples / column structure | Column (1) has no fixed effects; Column (2) adds IndustryFE and YearQtrFE | p.44: “IndustryFE N Y YearQtrFE N Y” | ✅ verified | pending | — |
| Winsorization / outliers | Variables winsorized at 1% | p.42: “Variables are winsorized at 1%.” | ✅ verified | pending | — |
| Reported sample size | N = 1,338 (Column 1); N = 1,325 (Column 2) | p.44: “N 1,338 1,325” | ✅ verified | pending | — |

\* required field
