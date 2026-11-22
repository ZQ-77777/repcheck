# Model Comparison

**Author** Xinyi Dou

**Experiment date** November 16, 2026

**Status** Scores and quote statuses rechecked against main `264fb4f` on November 21, 2026.

## Setup

We tested RepCheck's extraction on Tables 2 and 3 of Jayaraman and Wu (2020) using GPT-4.1 mini (`gpt-4.1-mini`), DeepSeek V4 Flash (`deepseek/deepseek-v4-flash-0731`), and DeepSeek V4 Pro (`deepseek/deepseek-v4-pro-0813`) through the HKUST GenAI (DDM 2026-27) API subscription. All baseline runs used the same PDF, the regression checklist template, prompt version `v1`, and the default 120-second client read timeout. [Paper DOI](https://doi.org/10.1093/rfs/hhz132)

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

A verified item passed automated quote matching. The reference-answer scores below assess answer text separately from quote matching.

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

PDF p.11 supports the Table 2 column-specific sample counts and fixed effects above. For Table 3 controls, p.14 refers to “Model 9 of Table 2”, while Table 2 has eight columns. D's reference notes interpret the citation as a numbering slip and use the full-controls specification in Model 8. Stable answers can still be wrong, and changes in evidence alone do not establish changes in answer meaning.

## Prompt Version Comparison

The specification prompt in `v2` asks for explicitly stated units and transformations, along with evidence for each detail. We evaluated the same three models and two tables as in the `v1` experiment. Each version had three planned attempts per model–table pair. The `v2` series ran sequentially with fresh caches, after the `v1` series. GPT-4.1 mini on Table 3 ran first for `v2`, and the second Flash Table 3 attempt was completed at the end. Differences in service load across the two series may affect timing and completion.

Both versions completed 17 of 18 attempts. The `v2` timeout was Flash on Table 3 in round 3 (123.110 seconds of wall-clock time). No balance reduction was visible at the subsequent check. The estimated total charge based on balance differences was HK$2.879931 for `v1` and HK$3.552697 for `v2`.

### Common metrics

The same criteria apply to both versions. We scored both versions against the same reference answers from [Part D PR #3](https://github.com/ZQ-77777/repcheck/pull/3), commit `0dc3c10`. The reference scores are detailed below, followed by the standardization results.

| Metric | v1 | v2 |
| --- | ---: | ---: |
| Successful attempts | 17/18 | 17/18 |
| Items passing automated quote matching | 189/221 | 188/221 |
| Total estimated charge (HKD) | 2.879931 | 3.552697 |
| Reported fields passing the automatic reference-answer check | 193/204 (94.6%) | 188/204 (92.2%) |

The quote-matching denominator is 17 successful checklists with 13 items each. A pass means the quote met the automated fuzzy-matching threshold (90), not necessarily a verbatim match. The verifier checks the cited page first, then other PDF pages and may correct the page number. This does not establish that the answer is correct or fully supported. Missing means the model did not return a value, not proof that the paper omits it. Reference-answer scoring compares answer text.

| Model | Table | v1 median successful time (s) | v2 median successful time (s) |
| --- | --- | ---: | ---: |
| GPT-4.1 mini | Table 2 | 16.511 | 19.965 |
| GPT-4.1 mini | Table 3 | 16.724 | 29.797 |
| DeepSeek V4 Flash | Table 2 | 56.492 | 56.767 |
| DeepSeek V4 Flash | Table 3 | 54.327 | 75.024 |
| DeepSeek V4 Pro | Table 2 | 64.930 | 89.550 |
| DeepSeek V4 Pro | Table 3 | 92.510 | 111.960 |

The median uses successful attempts. The v1 Pro Table 3 median and the v2 Flash Table 3 median each use two observations.

### Reference-answer scoring

We used the repository evaluator on the 34 saved checklists. It passes an answer when at least 60% of the distinct tokens in the shorter normalized answer also appear in the other answer. Each version has 17 successful checklists with 12 fields containing a reference answer, for 204 scored fields. In both versions all 17 winsorization fields were correctly left blank and are counted separately. Timeouts are excluded from field scores and retained in the completion results.

| Model | Table | v1 passed | v2 passed |
| --- | --- | ---: | ---: |
| GPT-4.1 mini | Table 2 | 31/36 | 33/36 |
| GPT-4.1 mini | Table 3 | 36/36 | 31/36 |
| DeepSeek V4 Flash | Table 2 | 33/36 | 35/36 |
| DeepSeek V4 Flash | Table 3 | 36/36 | 23/24 |
| DeepSeek V4 Pro | Table 2 | 33/36 | 32/36 |
| DeepSeek V4 Pro | Table 3 | 24/24 | 34/36 |

For the 16 model–table–round combinations completed in both versions, the scores were 181/192 for v1 and 177/192 for v2. Comparison with the observation counts printed in the PDF shows errors in both directions. Flash v1 round 2 on Table 2 passed the sample-size check with only 17,577, omitting 3,456 for column 6 and 17,505 for column 8 (PDF p.11). Flash v2 round 2 on Table 3 failed that check despite correctly reporting 7,770 for columns 1 and 3 and 9,570 for columns 2 and 4 (PDF p.14). Word overlap gives an automatic agreement score. The two examples illustrate why it can differ from agreement with the table.

### Standardization details in v2

This section measures how many of the requested standardization details v2 reported correctly. A comparison with v1 would require applying the same rubric to the v1 checklists.

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

## Recommendation

GPT-4.1 mini had the lowest median successful runtime on both tables. Flash had the lowest total estimated charge on both tables and more verified items per successful run than GPT-4.1 mini. Pro returned 12 verified items on every successful run and had one timeout. Keep Flash with v1 as the default for this project. It completed all six baseline runs, had the lowest estimated charge on both tables, and scored 69/72 against the references. Use v2 when standardization details are a priority and review the extracted details before reuse. In this experiment, v2 had a higher estimated total charge and a slightly lower automatic reference-answer pass rate. The two versions ran in separate batches with three planned attempts per model and table. Service conditions and the limitations of automatic scoring constrain what these differences tell us about the effect of the prompt change.

## Recheck after the B and D updates

We rechecked the saved runs against main `264fb4f`, including B's parser changes in PR #6 and D's follow-up in PR #7. The two reference-answer files and the scoring functions are unchanged from the versions used for the original scores. Parsing the same local PDF changed the text on page 17. For Tables 2 and 3, the target table metadata, selected pages and model-facing text remained identical. Keyword-hit metadata changed for page 17. Rechecking every saved quote against the updated full-PDF text preserved its matched status and page number. The totals remain 193/204 for v1 and 188/204 for v2. These are rescored historical runs, with the originally measured timing and charges. Validation on the updated code passed 64 tests and 10 subtests.

## Slide data

| Model (v1) | Completed | Median time, T2 / T3 | Estimated total cost (HKD) | Automatic reference check |
| --- | ---: | ---: | ---: | ---: |
| GPT-4.1 mini | 6/6 | 16.5 / 16.7 s | 0.28 | 67/72 |
| DeepSeek V4 Flash | 6/6 | 56.5 / 54.3 s | 0.14 | 69/72 |
| DeepSeek V4 Pro | 5/6 | 64.9 / 92.5 s | 2.47 | 57/60 |

Recommended default is Flash + v1 for this project. The optional v2 prompt correctly reported 49/76 standardization details, with direct quote support for 46. Times and reference scores use completed runs. Estimated costs include balance decreases observed around timeouts. The automatic reference check uses word overlap and can pass incomplete answers.
