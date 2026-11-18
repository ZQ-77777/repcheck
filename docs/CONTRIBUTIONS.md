# Contributions

Each member keeps their own section up to date. Link pull requests or commits. The README table and the
peer ratings are based on this file.

## Baseline (5 Nov 2026)
- v0.1 code, tests, synthetic examples and documents were drafted by Zhang Qi with AI assistance (Claude,
  Anthropic) as a starting point. Each module then has an owner who reviews, tests and extends it.

## Zhang Qi — coordination and integration
- Design of the two-stage tool and the interfaces in `schemas.py`; integration and releases.
- Real-paper case study (Jayaraman & Wu 2020): fixed run-together words in tightly typeset PDFs
  (false quote alarms 10 → 0 on Tables 2–3); added the "Subsamples / column structure" field after the
  paper showed it was missing; connected the HKUST GenAI API.
- Pull requests:

## Member B — PDF parsing and table locating
- Pull requests:

## Xinyi Dou (Member C) — prompts and model comparison
- Ran the sequential comparison of three models on JW2020 Tables 2 and 3 and analyzed the stability of the extracted answers and evidence.
- Added an optional v2 extraction prompt and compared runtime, estimated cost, quote matching and coverage of standardization details.
- Wrote the model comparison report. Field accuracy is pending review against the reference answers.

## Member D — evaluation and baseline
- Pull requests:

## Member E — interface
- Pull requests:

## Member F — result check and presentation
- Pull requests:
