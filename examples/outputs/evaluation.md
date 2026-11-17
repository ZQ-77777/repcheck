# Evaluation (live mode)

| Example | Fields correct | Wrong | Missed | Unreported → flagged missing | Invented | Quotes verified | Flagged for review | Result check |
|---|---|---|---|---|---|---|---|---|
| e1 | 13/13 | 0 | 0 | 0/0 | 0 | 15/16 | 1 | major differences: 7/11 coef. match, 7 issues |
| e2 | 11/11 | 0 | 0 | 2/2 | 0 | 12/12 | 0 | match: 7/7 coef. match, 0 issues |
| jw2020-t2 | 10/12 | 1 | 1 | 1/1 | 0 | 26/26 | 0 | not run (no results CSV) |
| jw2020-t3 | 12/12 | 0 | 0 | 1/1 | 0 | 17/17 | 0 | not run (no results CSV) |

## Failure cases

| Case | Input | Behaviour |
|---|---|---|
| f1 | Scanned PDF (no text layer) | ✅ ScannedPDFError: 'f1_scanned.pdf' has almost no extractable text (0 characters in 4 pages). It looks like a scanned PDF; please use a text-based PDF. |
| f2 | Table that does not exist (Table 9 in e1) | ✅ TableNotFoundError: Could not find 'Table 9' in the PDF. Tables found: Table 2, Table 3. |
| f3 | Results CSV with wrong columns | ✅ ResultsFormatError: Results CSV needs columns column, variable, coef; missing: coef, column, variable. |

## Per-field detail

### e1: e1_coverage_investment.pdf, Table 3

| Field | Check | Outcome vs gold |
|---|---|---|
| Sample period | verified | correct |
| Data sources | verified | correct |
| Sample filters | verified | correct |
| Unit of observation | verified | correct |
| Dependent variable | verified | correct |
| Key independent variable(s) | verified | correct |
| Control variables | verified | correct |
| Fixed effects | verified | correct |
| Standard errors | verified | correct |
| Estimation method | verified | correct |
| Subsamples / column structure | verified | correct |
| Winsorization / outliers | unverified | correct |
| Reported sample size | verified | correct |

### e2: e2_board_payout.pdf, TABLE II

| Field | Check | Outcome vs gold |
|---|---|---|
| Sample period | verified | correct |
| Data sources | verified | correct |
| Sample filters | verified | correct |
| Unit of observation | verified | correct |
| Dependent variable | verified | correct |
| Key independent variable(s) | verified | correct |
| Control variables | verified | correct |
| Fixed effects | verified | correct |
| Standard errors | missing | true_missing |
| Estimation method | verified | correct |
| Subsamples / column structure | verified | correct |
| Winsorization / outliers | missing | true_missing |
| Reported sample size | verified | correct |

### jw2020-t2: jw2020.pdf, Table 2

| Field | Check | Outcome vs gold |
|---|---|---|
| Sample period | verified | correct |
| Data sources | verified | correct |
| Sample filters | verified | correct |
| Unit of observation | verified | correct |
| Dependent variable | verified | correct |
| Key independent variable(s) | verified | wrong |
| Control variables | verified | correct |
| Fixed effects | verified | correct |
| Standard errors | verified | correct |
| Estimation method | missing | missed |
| Subsamples / column structure | verified | correct |
| Winsorization / outliers | missing | true_missing |
| Reported sample size | verified | correct |

### jw2020-t3: jw2020.pdf, Table 3

| Field | Check | Outcome vs gold |
|---|---|---|
| Sample period | verified | correct |
| Data sources | verified | correct |
| Sample filters | verified | correct |
| Unit of observation | verified | correct |
| Dependent variable | verified | correct |
| Key independent variable(s) | verified | correct |
| Control variables | verified | correct |
| Fixed effects | verified | correct |
| Standard errors | verified | correct |
| Estimation method | verified | correct |
| Subsamples / column structure | verified | correct |
| Winsorization / outliers | missing | true_missing |
| Reported sample size | verified | correct |
