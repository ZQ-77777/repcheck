# Baseline: gpt-4.1-mini, Table 3

## Question

I want to replicate Table 3 of this paper. List the sample period, data sources, sample filters, unit of observation, dependent variable, key independent variables, controls, fixed effects, standard errors, estimation method and winsorization, with page numbers.

## Answer (raw model, full paper in context)

Here is the detailed information to replicate Table 3 of the paper "Should I Stay or Should I Grow? Using Voluntary Disclosure to Elicit Market Feedback" by Sudarshan Jayaraman and Joanna Shuang Wu, with page references:

---

### Table 3: Higher/lower information asymmetry and positive/negative market reactions

---

#### Sample Period
- 2003 to 2015  
- (Page 8, Section 1.2 Data and sample; Page 13-14, Section 2.2 Cross-sectional tests)

#### Data Sources
- Capital expenditure (capex) forecasts: IBES Guidance  
- Accounting data: Compustat  
- Stock price data: CRSP  
- Probability of informed trading (PIN): Easley et al. (1996) data from Brown et al. (2004)  
- (Page 8, Section 1.2 Data and sample)

#### Sample Filters
- Start with 40,785 capex forecasts (2002-2016)  
- Match with CRSP for market reaction: 36,900 forecasts  
- Delete forecasts concurrent with earnings forecasts: 17,473  
- Delete forecasts in 2016 (no actual capex data): 1,850  
- Final sample: 17,577 capex forecasts by 1,790 firms (2003-2015)  
- (Page 8-9, Section 1.2 Data and sample)

#### Unit of Observation
- Firm-quarter  
- (Page 8, Section 1.2 Data and sample)

#### Dependent Variable
- CAPEX_ADJ: Percentage deviation of actual capital expenditures from forecasted capital expenditures, scaled by forecasted amount  
- (Page 8-9, Section 1.2 Data and sample; Table 1 Panel A)

#### Key Independent Variables
- CAR: Cumulative abnormal returns (CAR) over 5 days surrounding the capex forecast announcement (days [-2, 2]), standardized to zero mean and unit standard deviation  
- CAR_POS: Positive market reactions (CAR > 0), zero otherwise  
- CAR_NEG: Negative market reactions (CAR < 0), zero otherwise  
- (Page 9-10, Section 2.1 Regression model and main results; Page 13-14, Section 2.2 Cross-sectional tests)

#### Controls
- Full set of controls as in Model 9 of Table 2 (not fully tabulated in Table 3 for parsimony), including:  
  - Firm size (SIZE)  
  - Lagged capital expenditures (LAG_CAPX)  
  - Earnings surprise (SURP)  
  - Earnings announcement dummy (EA_DUM)  
- Market return on forecast date (MKTRET) and pseudo-market reaction (CAR_PRE) included in other models but not in Table 3  
- (Page 10-12, Section 2.1 Regression model and main results; Page 13-14, Section 2.2 Cross-sectional tests)

#### Fixed Effects
- Firm fixed effects  
- Year-quarter fixed effects  
- (Page 10, Section 2.1 Regression model and main results; Table 3 notes)

#### Standard Errors
- Robust standard errors clustered by industry  
- (Page 10, Section 2.1 Regression model and main results; Table 3 notes)

#### Estimation Method
- Panel regression (linear regression) of CAPEX_ADJ on CAR and controls with fixed effects  
- CAR split into CAR_POS and CAR_NEG in some models  
- (Page 10-12, Section 2.1 Regression model and main results; Page 13-14, Section 2.2 Cross-sectional tests)

#### Winsorization
- Not explicitly mentioned for Table 3 variables; however, standard practice in finance papers is to winsorize variables at 1% or 0.5% tails. The paper mentions winsorization in other contexts but does not specify for Table 3.  
- (No explicit page reference; implied standard practice)

---

### Summary of Table 3 Results (Page 13-14)

- The sample is split based on changes in information asymmetry measured by bid-ask spreads around the forecast announcement:  
  - Lower spreads (decrease in information asymmetry)  
  - Higher spreads (increase in information asymmetry)  
- CAR coefficient is positive and significant only in the "Higher spreads" subsample (Model 2), insignificant and negative in "Lower spreads" (Model 1).  
- CAR_POS (positive returns) is significant and positive only in "Higher spreads" (Model 4), CAR_NEG (negative returns) insignificant in both subsamples.  
- The difference in CAR coefficients between subsamples is statistically significant at 5% level.  
- These results support the hypothesis that feedback effects are stronger when disclosure increases information asymmetry and for positive market reactions.  

---

### Exact Citation for Table 3

- Table 3 is on **Page 13-14** of the paper (pages 3866-3867 in the journal pagination).

---

If you need further details on variable definitions or regression specifications, please let me know!
