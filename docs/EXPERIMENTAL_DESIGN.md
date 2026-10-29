# Experimental design (pilot)

## Baseline matrix (smoke, CPU)

Configs in `rageval/benchmark/suite.py`, `configs/ablation/`, and named slices in `configs/experiments/` (A_chunk … G_claim_vs_answer).

1. Dense chunk 128  
2. Dense chunk 256 (baseline)  
3. Dense chunk 512  
4. BM25 chunk 256  
5. Hybrid RRF chunk 256  
6. Hybrid RRF + cross-encoder rerank (optional / slower)

Generator: blinded mock, `faithful` mode, `empty_context` abstention.  
Verifier: `nli` with DeBERTa-v3; heuristic only when `method: heuristic`.  
Embedder: `sentence-transformers/all-MiniLM-L6-v2`.

## Dataset

- **smoke_v1**: 8 synthetic documents, 8 items (`data/cards/smoke_v1.md`). Development fixture and CI. Not for publication claims.
- **benchmark_v1**: v1.1.0 is 18 licensed documents, 28 items (`data/cards/benchmark_v1.md`). Mix of U.S. government public-domain excerpts and original CC-BY-4.0 fiction. Documented 20/8 dev/test split (test ids frozen from v1.0.0). The first ablation reports the **full v1.0.0 24-item set** because n_test=8 is underpowered.

## Analysis plan

1. Per-config means of retrieval and claim metrics on the same items.
2. Do not run significance tests on \(n=8\) or \(n=24\) as confirmatory results.
3. Qualitative cases: mixed-support, unanswerable, conflicting. Phase 6 adds robustness-by-scenario and `reports/error_analysis_phase6.md`.
4. Report generator blinding (RQ4) as an engineering check on the mock.
5. RQ2 verifier scores live in `reports/verifier_eval_v1.md` (n=24 labeled pairs). On this set DeBERTa macro-F1 was 0.692 and the lexical heuristic 0.514. Partial-support F1 was 0.0 for NLI. This does not confirm RQ2 beyond the labeled set.

## Exclusions

No paid API runs unless separately approved. No silent model fallback.
