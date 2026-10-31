# Known limitations (0.2.1)

Longer threats list: `docs/RESEARCH_GAPS.md`. Published v1.0.0 write-up: `reports/20261028T183042Z_a97ad68f/FINDINGS.md`. Companion v1.1.0: `reports/20261029T165024Z_657c8089/FINDINGS.md`. Companion v1.2.0: `reports/20261029T173408Z_de870a29/FINDINGS.md`.

- Official generator is a **blinded mock**, not an LLM. Live NVIDIA NIM companions: smoke `20261030T052448Z_6df3afb9`; sparse `20261030T052638Z_79a8b21d` (faith 0.7188); dense/hybrid `20261030T055224Z_388c5503` (dense 0.7396, hybrid 0.6458). R@5 stays 0.8438. They are not the published ablation. `rageval score` accepts run `predictions.jsonl`. `rageval compare` diffs two `per_example.jsonl` files.
- Official published ablation is **n=24** items / 16 documents (`20261028T183042Z_a97ad68f`); items share documents; tests are underpowered.
- Companion v1.1.0 run `20261029T165024Z_657c8089` scores all 28 items (18 documents) with the same blinded mock + DeBERTa setup. n=28 is still underpowered. It does not replace the published table.
- Current corpus is `benchmark_v1` **1.3.0** (29 documents, 40 items). Companion run `20261029T173408Z_de870a29` scores the 1.2.0 32-item set (overlap 16/32/64). `A_chunk` overlap-32 is `20261029T173515Z_7e2b94a3`. v1.3.0 has no recorded NLI companion yet. n=40 is still underpowered on the full set because items share documents. None of these replace the published table.
- Single-author gold. IAA CLI and kappa exist (`rageval iaa`). Rater B is a disclosed LLM (`rater_b_llm_grok`, kappa 0.9423 on n=24); that is diagnostic, not confirmatory human IAA. An independent human can fill labels with `rageval iaa-label` onto a new file such as `annotator_b_human.json`.
- Faithfulness is support-by-retrieved-evidence, not world truth.
- Cost is null unless `EvaluatorConfig` sets prices **and** `pricing_source`.
- This project is not Niu et al. 2024 RAGTruth.
- HTTP jobs are process-local (one thread, one job). There is no Redis/Celery queue. Default HTTP config is smoke; a full NLI ablation needs `allow_heavy=true` (dashboard checkbox) or the CLI. The dashboard Start button uses that same queue. Live `/evaluate/answer` and `/score` default to heuristic. Software production notes: `docs/PRODUCTION.md`.
- `requirements-lock-all.txt` is manylinux x86_64 CPU torch. It does not pin CUDA wheels and does not make NLI logits identical across machines.
- Fast GitHub CI skips `-m hf`. Trust the weekly/manual workflow (cached HF hub) for DeBERTa/MiniLM/reranker. First green run: https://github.com/Aaravkhanal/RAGEVAL/actions/runs/40891849818
