# Known limitations (0.2.1)

Longer threats list: `docs/RESEARCH_GAPS.md`. Honest v1 write-up: `reports/20261028T183042Z_a97ad68f/FINDINGS.md`.

- Official generator is a **blinded mock**, not an LLM. `openai` / `ollama` / `local_hf` exist as opt-in backends (`configs/opt_in/`); they are not the recorded ablation.
- Recorded ablation is **n=24** items / 16 documents; items share documents; tests are underpowered.
- Single-author gold; no IAA.
- Faithfulness is support-by-retrieved-evidence, not world truth.
- Cost is null unless `EvaluatorConfig` sets prices **and** `pricing_source`.
- v1.1.0 items `v1_025`–`v1_028` are unscored in run `20261028T183042Z_a97ad68f`.
- This project is not Niu et al. 2024 RAGTruth.
- HTTP jobs are process-local (one thread, one job). There is no Redis/Celery queue. Default HTTP config is smoke; a full NLI ablation needs `allow_heavy=true` (dashboard checkbox) or the CLI. The dashboard Start button uses that same queue.
- `requirements-lock-all.txt` is manylinux x86_64 CPU torch. It does not pin CUDA wheels and does not make NLI logits identical across machines.
- Fast GitHub CI skips `-m hf`. Trust the weekly/manual workflow (cached HF hub) for DeBERTa/MiniLM/reranker. First green run: https://github.com/Aaravkhanal/RAGEVAL/actions/runs/40891849818
