# Known limitations (0.2.1)

Longer threats list: `docs/RESEARCH_GAPS.md`. Published v1.0.0 write-up: `reports/20261028T183042Z_a97ad68f/FINDINGS.md`. Companion v1.1.0: `reports/20261029T165024Z_657c8089/FINDINGS.md`.

- Official generator is a **blinded mock**, not an LLM. `openai` / `ollama` / `local_hf` exist as opt-in backends (`configs/opt_in/`); they are not the recorded ablation. A live LLM smoke was not run; see `reports/opt_in_smoke_llm/STATUS.md`.
- Official published ablation is **n=24** items / 16 documents (`20261028T183042Z_a97ad68f`); items share documents; tests are underpowered.
- Companion v1.1.0 run `20261029T165024Z_657c8089` scores all 28 items (18 documents) with the same blinded mock + DeBERTa setup. n=28 is still underpowered. It does not replace the published table.
- Current corpus is `benchmark_v1` **1.2.0** (21 documents, 32 items). New ids `v1_029`–`v1_032` are unscored vs `657c8089`. The six-config NLI matrix was not re-run.
- Single-author gold. IAA CLI and kappa exist (`rageval iaa`); rater B is still missing, so confirmatory IAA is not reported.
- Faithfulness is support-by-retrieved-evidence, not world truth.
- Cost is null unless `EvaluatorConfig` sets prices **and** `pricing_source`.
- This project is not Niu et al. 2024 RAGTruth.
- HTTP jobs are process-local (one thread, one job). There is no Redis/Celery queue. Default HTTP config is smoke; a full NLI ablation needs `allow_heavy=true` (dashboard checkbox) or the CLI. The dashboard Start button uses that same queue.
- `requirements-lock-all.txt` is manylinux x86_64 CPU torch. It does not pin CUDA wheels and does not make NLI logits identical across machines.
- Fast GitHub CI skips `-m hf`. Trust the weekly/manual workflow (cached HF hub) for DeBERTa/MiniLM/reranker. First green run: https://github.com/Aaravkhanal/RAGEVAL/actions/runs/40891849818
