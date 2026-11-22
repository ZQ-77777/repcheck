# Handover log

One entry per handover exercise. The README needs only the most useful lesson.

Plan:
- H1 (done): Tang Yunshu (B) → Xu Fanqi (D) — D runs the tool on an unseen paper using only B's module docstrings and tests.
- H2: Zhang Qi → Zhou Zhenyu — Zhou runs the whole demo on Zhang Qi's laptop using only the README and the script.

<<<<<<< HEAD
### H1: Tang Yunshu (B) → Xu Fanqi (D), 2026-11-19
=======
### H1: B → D, 2026-11-19
>>>>>>> 3ad900c83ade00f30e2a7bdcfcba7ef62a33b8f4
- Task: Run the full evaluation on a paper the tool had never seen (Jha, Qian, Weber & Yang 2024,
  "ChatGPT and Corporate Policies", NBER WP 32161, open access; 17 tables, tables at the end of
  a 70-page PDF), using only B's module docstrings (`table_locator.py`) and tests
  (`tests/test_parser_locator.py`) — no implementation reading. Run against main `59f4da7`;
  B's extension PR had not landed by the freeze, so this exercises the module as merged.
- Time taken: ~15 minutes end to end (4 s to list all 17 tables; 39 s for the live extraction;
  one 2-minute API read-timeout retry on the way, unrelated to the locator).
- What made it easy: The docstring states input, output and error behaviour in five lines, and
  the tests double as a usage manual (label variants "Table 3"/"3"/"table III", spacing variants
  "Table3"/"T able 3", the "table not found lists alternatives" contract). Two CLI commands
  (`tables`, `spec`) were enough — no need to open the implementation. The locator handled a
  caption style absent from our examples ("Table 2. ChatGPT Predictions vs. CFO Survey
  Results" — period plus a long title) without any change.
- What made it hard: The two `missing` fields (controls, estimation method) required going back
  to the paper to decide "genuinely unreported vs. model missed" — the keyword hints point to
  plausible pages, but the judgement stays with the human, which is by design. The API
  read-timeout needed one retry (network, not the module).
- Outcome: Table 2 located on p.44, 11/13 fields verified, 13/13 quotes verified by the
  program (including table-transcribed evidence such as "N 1,338 1,325"). Output in
  `examples/outputs/handover/nber32161/`.
- Change made afterwards: none needed — the module behaved as documented.

  Re-check after B's PR #6 landed (2026-11-21, main `655acf5`): the same two commands on the
  same NBER paper reproduce the original H1 run exactly (17 tables; Table 2 on p.44;
  11 verified / 2 missing; checklist values, statuses and quotes identical) — the sideways-page
  changes are backward compatible. Also confirmed on JW2020: Table 4 (printed sideways) now
  appears in `cli.py tables`, closing the known issue of 2026-11-16.
<<<<<<< HEAD

### H2: Zhang Qi → Zhou Zhenyu, 2026-11-__
- Task: run the full demo (JW2020 Table 3, then Example 1) on Zhang Qi's laptop using only the README and the script.
- Time taken:
- What made it easy:
- What made it hard:
- Change made afterwards:
=======
>>>>>>> 3ad900c83ade00f30e2a7bdcfcba7ef62a33b8f4
