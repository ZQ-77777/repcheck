# Replication checklist — Table 3

- Paper: Analyst Coverage and Corporate Investment
- Table: Table 3 Analyst Coverage and Corporate Investment (PDF page 4)
- Model: deepseek/deepseek-v4-flash-0731 · template: regression · exported 2026-11-17 19:18
- Review complete: NO — pending items remain

| Field | Extracted value | Evidence | Check | Review | Final value |
|---|---|---|---|---|---|
| Sample period * | 2003-2019 | p.2: “Our sample covers fiscal years 2003 to 2019.” | ✅ verified | pending | — |
| Data sources * | • Compustat (financial statements)<br>• CRSP (stock prices)<br>• I/B/E/S (analyst coverage) | p.2: “We obtain financial statement data from Compustat, stock price data from CRSP, and analyst coverage from I/B/E/S.” | ✅ verified | pending | — |
| Sample filters * | • Exclude financial firms (SIC 6000-6999)<br>• Exclude utilities (SIC 4900-4999)<br>• Require non-missing values for all regression variables<br>• Require lagged total assets of at least $10 million | p.2: “We exclude financial firms (SIC codes 6000-6999) and utilities (SIC codes 4900-4999)”<br>p.2: “We require non-missing values for all regression variables and lagged total assets of at least $10 million.” | ✅ verified | pending | — |
| Unit of observation * | firm-year | p.2 (corrected): “The unit of observation is the firm-year.” | ✅ verified<br>*Page number corrected to p.2.* | pending | — |
| Dependent variable * | INVEST: Capital expenditures (CAPX) in year t+1 divided by total assets (AT) in year t | p.5: “INVEST Capital expenditures (CAPX) in year t+1 divided by total assets (AT) in year t.” | ✅ verified | pending | — |
| Key independent variable(s) * | • COVERAGE: Natural log of one plus the number of analysts with an annual EPS forecast (I/B/E/S) | p.5: “COVERAGE Natural log of one plus the number of analysts with an annual EPS forecast (I/B/E/S).” | ✅ verified | pending | — |
| Control variables * | • SIZE: Natural log of total assets (AT)<br>• LEV: Long-term debt plus debt in current liabilities (DLTT + DLC) divided by AT<br>• MTB: Market value of equity (PRCC_F x CSHO) divided by book equity (CEQ)<br>• CASH: Cash and short-term investments (CHE) divided by AT<br>• ROA: Income before extraordinary items (IB) divided by AT | p.5: “SIZE Natural log of total assets (AT).”<br>p.5: “ROA Income before extraordinary items (IB) divided by AT.”<br>p.3: “Column (2) adds SIZE, LEV and MTB, and column (3) further adds CASH and ROA.” | ✅ verified | pending | — |
| Fixed effects * | Firm and year fixed effects | p.3: “Firm fixed effects absorb time-invariant differences in investment policy, and year fixed effects absorb aggregate shocks.” | ✅ verified | pending | — |
| Standard errors * | Clustered at the firm level | p.3: “Standard errors are clustered at the firm level.” | ✅ verified | pending | — |
| Estimation method * | OLS | p.3: “We estimate all models using ordinary least squares (OLS).” | ✅ verified | pending | — |
| Subsamples / column structure | Same sample in all columns; column 1 includes only COVERAGE, column 2 adds SIZE, LEV and MTB, column 3 adds CASH and ROA | p.3: “Column (2) adds SIZE, LEV and MTB, and column (3) further adds CASH and ROA.” | ✅ verified | pending | — |
| Winsorization / outliers | Continuous variables winsorized at the 1% and 99% levels | p.2 ⚠️: “All continuous variables are winsorized at 1% and 99% to remove outliers.” | ⚠️ unverified<br>*1 quote(s) could not be found in the PDF text — the value may be paraphrased or invented. Check p.2 before confirming.* | pending | — |
| Reported sample size | 24,318 firm-year observations | p.4: “Observations 24,318 24,318 24,318” | ✅ verified | pending | — |

\* required field
