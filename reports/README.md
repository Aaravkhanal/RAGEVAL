# Reports snapshot

**Run id:** `20261028T183042Z_a97ad68f`  
**Dataset:** `benchmark_v1` 1.0.0 (16 documents, 24 items, split=`all`)  
**Generator:** blinded mock (`faithful`, `empty_context` abstention)  
**Verifier:** DeBERTa-v3 NLI (`allow_heuristic_fallback=false`)  
**Cost:** null (no pricing configured)

The unique run folder is local (`experiments/runs/` is gitignored). This directory is the committed table/figure snapshot of that run.

Phase 6 error analysis for this run’s adversarial slice: `reports/error_analysis_phase6.md`. It does not invent scores for v1.1.0 items.

Phase 7 labeled tables generated from this run’s summaries: `reports/phase7/`.

The process started from git commit `3f8d3a3` with **uncommitted** `benchmark_v1` files in the working tree. Re-run after this commit to pin the same data to a commit hash.

`paper.tex` remains a draft and is not evidence.

## How to read the table

- Retrieval Recall@5 and MRR are **identical** across the six configs on this 16-document corpus. RQ1 retrieval differences are not identifiable here.
- Answer EM is 0.0: the mock copies retrieved sentences and does not match gold strings exactly.
- Mixed-support token F1 is 0.6292 on all configs while mixed-support claim faithfulness ranges 0.375–0.625 (RQ3 slice, n=4).
- Abstention accuracy is 0.0: unanswerable items still retrieved context, and the blinded mock does not see `test_type`.
