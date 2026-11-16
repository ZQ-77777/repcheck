# Model Comparison

**Author** Xinyi Dou

**Experiment date** November 16, 2026

**Status** Sequential runs complete. Field accuracy pending review against the reference answers.

## Setup

We tested RepCheck's extraction on Tables 2 and 3 of Jayaraman and Wu (2020) using GPT-4.1 mini (`gpt-4.1-mini`), DeepSeek V4 Flash (`deepseek/deepseek-v4-flash-0731`), and DeepSeek V4 Pro (`deepseek/deepseek-v4-pro-0813`) through the HKUST GenAI (DDM 2026-27) API subscription. All runs used the same PDF, the regression checklist template, prompt version `v1`, and the default 120-second client read timeout. [Paper DOI](https://doi.org/10.1093/rfs/hhz132)

For the v1 benchmark, each round covered all six model–table pairs in a different order. We sent requests one at a time and used a separate cache and output directory for each attempt. All benchmark results below come from these sequential runs.

## Results

**17 of 18 planned attempts succeeded.** DeepSeek V4 Pro timed out on Table 3 in round 3. The estimated total charge was **HK$2.879931**, including the HK$0.316947 balance decrease recorded around the timeout. Charges are estimated from the change in API credit between attempts. Elapsed time is the terminal's wall-clock time for the full command.

| Run | Status | Verified | Unverified | Missing | Elapsed (s) | Estimated charge (HKD) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `r1-gpt-t2` | Success | 11 | 1 | 1 | 17.603 | 0.047869 |
| `r1-flash-t2` | Success | 12 | 0 | 1 | 119.390 | 0.020519 |
| `r1-pro-t2` | Success | 12 | 0 | 1 | 64.930 | 0.344278 |
| `r1-gpt-t3` | Success | 9 | 3 | 1 | 19.977 | 0.045514 |
| `r1-flash-t3` | Success | 11 | 1 | 1 | 37.264 | 0.020841 |
| `r1-pro-t3` | Success | 12 | 0 | 1 | 104.070 | 0.624014 |
| `r2-flash-t3` | Success | 12 | 0 | 1 | 54.327 | 0.036169 |
| `r2-pro-t3` | Success | 12 | 0 | 1 | 80.950 | 0.407591 |
| `r2-gpt-t3` | Success | 10 | 2 | 1 | 16.639 | 0.046410 |
| `r2-flash-t2` | Success | 11 | 1 | 1 | 56.492 | 0.020895 |
| `r2-pro-t2` | Success | 12 | 0 | 1 | 109.270 | 0.309291 |
| `r2-gpt-t2` | Success | 9 | 3 | 1 | 16.511 | 0.044016 |
| `r3-pro-t2` | Success | 12 | 0 | 1 | 60.770 | 0.464619 |
| `r3-gpt-t2` | Success | 10 | 2 | 1 | 16.371 | 0.044822 |
| `r3-flash-t2` | Success | 12 | 0 | 1 | 40.712 | 0.013546 |
| `r3-pro-t3` | Read timeout | — | — | — | 124.610 | 0.316947 |
| `r3-gpt-t3` | Success | 10 | 2 | 1 | 16.724 | 0.046422 |
| `r3-flash-t3` | Success | 12 | 0 | 1 | 100.090 | 0.026168 |

| Model | Table | Successful attempts | Verified per successful run | Median successful time (s) | Total estimated charge (HKD) |
| --- | --- | ---: | --- | ---: | ---: |
| DeepSeek V4 Flash | Table 2 | 3/3 | 12, 11, 12 | 56.492 | 0.054960 |
| DeepSeek V4 Flash | Table 3 | 3/3 | 11, 12, 12 | 54.327 | 0.083178 |
| DeepSeek V4 Pro | Table 2 | 3/3 | 12, 12, 12 | 64.930 | 1.118188 |
| DeepSeek V4 Pro | Table 3 | 2/3 | 12, 12 | 92.510 | 1.348552 |
| GPT-4.1 mini | Table 2 | 3/3 | 11, 9, 10 | 16.511 | 0.136707 |
| GPT-4.1 mini | Table 3 | 3/3 | 9, 10, 10 | 16.724 | 0.138346 |

A verified item passed automated quote matching. Field accuracy is pending for all 17 successful runs. It requires checking that the extracted answer and its evidence apply to the target table and model column.

## Stability

We compared the stored answers and evidence by field across the successful runs. Exact comparisons count wording changes. A field can appear in both columns. Pro Table 3 has two available checklists.

| Model | Table | Fields with answer changes | Fields with evidence changes |
| --- | --- | --- | --- |
| DeepSeek V4 Flash | Table 2 | Data sources, Sample filters, Control variables, Fixed effects, Standard errors, Subsamples / column structure, Reported sample size | Data sources, Sample filters, Key independent variable(s), Control variables, Estimation method, Subsamples / column structure, Reported sample size |
| DeepSeek V4 Flash | Table 3 | Sample period, Data sources, Sample filters, Dependent variable, Control variables, Standard errors, Subsamples / column structure, Reported sample size | Data sources, Sample filters, Dependent variable, Key independent variable(s), Control variables, Fixed effects, Standard errors, Estimation method, Subsamples / column structure |
| DeepSeek V4 Pro | Table 2 | Sample period, Data sources, Sample filters, Key independent variable(s), Control variables, Fixed effects, Standard errors, Estimation method, Subsamples / column structure, Reported sample size | Data sources, Sample filters, Key independent variable(s), Control variables, Fixed effects, Estimation method, Subsamples / column structure |
| DeepSeek V4 Pro | Table 3 | Sample filters, Control variables, Fixed effects, Standard errors, Subsamples / column structure, Reported sample size | Data sources, Sample filters, Key independent variable(s), Control variables, Estimation method, Subsamples / column structure |
| GPT-4.1 mini | Table 2 | Data sources, Sample filters, Key independent variable(s), Control variables, Standard errors, Subsamples / column structure | Sample filters, Dependent variable, Key independent variable(s), Control variables, Fixed effects, Standard errors, Subsamples / column structure |
| GPT-4.1 mini | Table 3 | Data sources, Sample filters, Subsamples / column structure | Sample filters, Control variables, Fixed effects, Standard errors, Subsamples / column structure |

### Interpretation of the observed differences

We read the changed answer fields in all six v1 model–table groups. The table above measures textual variation, not a semantic error rate. The following examples distinguish wording from differences in information coverage. A third type is an answer conflict: two runs make incompatible claims about the same detail for the same column. The examples below illustrate wording and coverage differences. They do not provide a count of conflicts or replace scoring against D's reviewed reference answers.

| Model / table | Wording or equivalent presentation | Information coverage differences |
| --- | --- | --- |
| GPT-4.1 mini / Table 2 | Data-source names and most sample-filter phrasing | Round 3 adds the CAR event window. Round 2 lists SF_CAR, MKTRET and CAR_PRE under controls; rounds 1 and 3 do not. Column and clustering detail also varies. |
| GPT-4.1 mini / Table 3 | The changed source descriptions, filter wording and spread-group descriptions largely preserve the same core meaning | Round 2 explicitly interprets lower/higher spreads as decreases/increases in information asymmetry. Text differences alone do not show contradictory answers. |
| Flash / Table 2 | Reordering the same fixed-effect descriptions in rounds 1 and 3 | Round 2 omits the log definition of SIZE, column-specific fixed effects, and separate observation counts. PDF p.11 gives 3,456 for column 6 and 17,505 for column 8, in addition to 17,577 for the other columns. |
| Flash / Table 3 | “2003-2015” versus “2003 to 2015”; equivalent CAPEX_ADJ wording | PIN appears as a source only in round 1. Control definitions, event windows and sample-size labels vary in detail. Source relevance requires reference-answer review. |
| Pro / Table 2 | Dash styles, fixed-effect wording, clustering wording and identical sample counts | PIN is absent in round 3; CAR and SIZE definitions and filtering counts vary in detail. |
| Pro / Table 3 | Capitalization of fixed effects and standard errors; equivalent sample-filter descriptions | SF_CAR is listed as a control only in round 1. Round 2 adds column labels to sample counts. |

PDF p.11 supports the Table 2 column-specific sample counts and fixed effects above. For Table 3 controls, p.14 refers to “Model 9 of Table 2”, while Table 2 has eight columns. We retain this source ambiguity for D to resolve rather than treating a varying control list as conclusively correct or incorrect. Stable answers can still be wrong, and changes in evidence alone do not establish changes in answer meaning.

## Prompt Version Comparison

The specification prompt in `v2` asks for explicitly stated units and transformations, along with evidence for each detail. We evaluated the same three models and two tables as in the `v1` experiment. Each version had three planned attempts per model–table pair. The `v2` series ran sequentially with fresh caches, after the `v1` series. GPT-4.1 mini on Table 3 ran first for `v2`, and the second Flash Table 3 attempt was completed at the end. Differences in service load across the two series may affect timing and completion.

Both versions completed 17 of 18 attempts. The `v2` timeout was Flash on Table 3 in round 3 (123.110 seconds of wall-clock time). No balance reduction was visible at the subsequent check. The estimated total charge based on balance differences was HK$2.879931 for `v1` and HK$3.552697 for `v2`.

### Common metrics

The same criteria apply to both versions. Field accuracy for the original checklist requirements will be scored using the same reviewed reference answers. The next section assesses standardization details requested by v2.

| Metric | v1 | v2 |
| --- | ---: | ---: |
| Successful attempts | 17/18 | 17/18 |
| Items passing automated quote matching | 189/221 | 188/221 |
| Total estimated charge (HKD) | 2.879931 | 3.552697 |
| Accuracy on shared checklist requirements | Pending | Pending |

The quote-matching denominator is 17 successful checklists with 13 items each. A pass means the quote met the automated fuzzy-matching threshold (90), not necessarily a verbatim match. The verifier checks the cited page first, then other PDF pages and may correct the page number. This does not establish that the answer is correct or fully supported. Missing means the model did not return a value, not proof that the paper omits it. Field scoring also checks what the quote supports.

| Model | Table | v1 median successful time (s) | v2 median successful time (s) |
| --- | --- | ---: | ---: |
| GPT-4.1 mini | Table 2 | 16.511 | 19.965 |
| GPT-4.1 mini | Table 3 | 16.724 | 29.797 |
| DeepSeek V4 Flash | Table 2 | 56.492 | 56.767 |
| DeepSeek V4 Flash | Table 3 | 54.327 | 75.024 |
| DeepSeek V4 Pro | Table 2 | 64.930 | 89.550 |
| DeepSeek V4 Pro | Table 3 | 92.510 | 111.960 |

The median uses successful attempts. The v1 Pro Table 3 median and the v2 Flash Table 3 median each use two observations.

### Standardization details in v2

These checks assess compliance with the additional v2 request, not overall superiority to v1. V1 did not explicitly request all these details. Additional correct information indicates useful guidance, but completeness, shared-field accuracy, runtime and cost must be considered separately.

We checked all 17 successful v2 checklists against the PDF. We counted each correctly reported standardized variable once per checklist and then checked whether a quote attached anywhere in that checklist directly supported it. Table 2 lists four standardized variables on PDF page 11 (CAR, SF_CAR, MKTRET, CAR_PRE). Table 3 lists five on PDF page 14 (CAR, CAR_POS, CAR_NEG, MKTRET, CAR_PRE). In Table 3, CAR appears at the end of the preceding line in the PDF.

| Model | Table | Checklists | Standardizations reported correctly | Of those, directly supported |
| --- | --- | ---: | ---: | ---: |
| GPT-4.1 mini | Table 2 | 3 | 3/12 | 0 |
| GPT-4.1 mini | Table 3 | 3 | 0/15 | 0 |
| DeepSeek V4 Flash | Table 2 | 3 | 9/12 | 9 |
| DeepSeek V4 Flash | Table 3 | 2 | 10/10 | 10 |
| DeepSeek V4 Pro | Table 2 | 3 | 12/12 | 12 |
| DeepSeek V4 Pro | Table 3 | 3 | 15/15 | 15 |

- **Standardization.** In total, the outputs recovered 49 of 76 checklist-level standardization details. Direct quotes supported 46 of those 49. The three GPT-4.1 mini Table 2 checklists correctly identified CAR standardization, but their supplied quotes joined fragments that did not reproduce the relevant passage verbatim.

## Provisional recommendation

GPT-4.1 mini had the lowest median successful runtime on both tables. Flash had the lowest total estimated charge on both tables and more verified items per successful run than GPT-4.1 mini. Pro returned 12 verified items on every successful run and had one timeout. Flash is a candidate for the default if the reference-answer review confirms adequate field accuracy and completeness. With three planned attempts per pair, the timings and success counts describe this experiment.
