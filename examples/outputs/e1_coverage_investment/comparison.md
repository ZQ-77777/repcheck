# Replication check — Table 3

**Overall: major differences** · 7/11 coefficients match (sign, magnitude and significance)

⚠️ These paper numbers could not be verified on the table page (possible transcription error — check before trusting the comparison): (2) LEV=-0.0452***

| Column | Variable | Type | Severity | Paper | Replication | What it suggests |
|---|---|---|---|---|---|---|
| (1) | — | n_mismatch | major | 24,318 | 23,104 | N differs by -5.0%; coefficient differences in this column may follow from the sample difference. |
| (2) | — | n_mismatch | major | 24,318 | 23,104 | N differs by -5.0%; coefficient differences in this column may follow from the sample difference. |
| (2) | MTB | se_mismatch | minor | (0.0011) | 0.003 | Standard errors differ by 172.7%. Check the clustering level and the standard-error estimator. |
| (2) | MTB | significance | minor | 0.0064*** (3 stars) | 2 stars | Significance level differs — check standard errors / clustering. |
| (3) | — | n_mismatch | major | 24,318 | 23,104 | N differs by -5.0%; coefficient differences in this column may follow from the sample difference. |
| (3) | LEV | magnitude | major | -0.0398*** | -0.0286 | Magnitude differs by 28%. |
| (3) | CASH | scale | major | 0.0311** | 3.08 | Off by a factor of about 99 — likely a units/scaling difference (e.g. percent vs. fraction). |
| (3) | ROA | variable_missing | major | 0.0874*** | — | ROA is in the paper but not in the replication. |

## Where to look first

**Sample size differs** (3× in columns (1), (2), (3)) — re-check:
- Sample filters: Exclude financial firms (SIC 6000-6999); Exclude utilities (SIC 4900-4999); Require non-missing values for all regression variables; Require lagged total assets of at least $10 million (p.2)
- Subsamples / column structure: Same sample in all columns; column 1 includes only COVERAGE, column 2 adds SIZE, LEV and MTB, column 3 adds CASH and ROA (p.3)
- Sample period: 2003-2019 (p.2)
- Data sources: Compustat (financial statements); CRSP (stock prices); I/B/E/S (analyst coverage) (p.2)

**Variables missing from the replication** (1× in column (3)) — re-check:
- Control variables: ROA: Income before extraordinary items (IB) divided by AT (p.3, p.5)

**Units / scaling differ** (1× in column (3)) — re-check:
- Control variables: CASH: Cash and short-term investments (CHE) divided by AT (p.3, p.5)

**Coefficient magnitudes differ** (1× in column (3)) — re-check:
- Winsorization / outliers: Continuous variables winsorized at the 1% and 99% levels (p.2)
- Subsamples / column structure: Same sample in all columns; column 1 includes only COVERAGE, column 2 adds SIZE, LEV and MTB, column 3 adds CASH and ROA (p.3)
- Control variables: LEV: Long-term debt plus debt in current liabilities (DLTT + DLC) divided by AT (p.3, p.5)
- Sample filters: Exclude financial firms (SIC 6000-6999); Exclude utilities (SIC 4900-4999); Require non-missing values for all regression variables; Require lagged total assets of at least $10 million (p.2)
- Fixed effects: Firm and year fixed effects (p.3)

**Significance levels differ** (1× in column (2)) — re-check:
- Standard errors: Clustered at the firm level (p.3)
- Fixed effects: Firm and year fixed effects (p.3)

**Standard errors differ** (1× in column (2)) — re-check:
- Standard errors: Clustered at the firm level (p.3)
