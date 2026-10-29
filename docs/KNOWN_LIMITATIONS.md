# Known limitations (release candidate)

Longer threats list: `docs/RESEARCH_GAPS.md`. Honest v1 write-up: `reports/20261028T183042Z_a97ad68f/FINDINGS.md`.

- Official generator is a **blinded mock**, not an LLM.
- Recorded ablation is **n=24** items / 16 documents; items share documents; tests are underpowered.
- Single-author gold; no IAA.
- Faithfulness is support-by-retrieved-evidence, not world truth.
- Cost is null unless `EvaluatorConfig` sets prices **and** `pricing_source`.
- v1.1.0 items `v1_025`–`v1_028` are unscored in run `20261028T183042Z_a97ad68f`.
- This project is not Niu et al. 2024 RAGTruth.
- HTTP jobs are process-local (one thread, one job). There is no Redis/Celery queue. Default HTTP config is smoke; a full NLI ablation needs `allow_heavy=true` or the CLI.
