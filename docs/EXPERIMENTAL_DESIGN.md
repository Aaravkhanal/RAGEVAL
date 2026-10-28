# Experimental design (pilot)

## Baseline matrix (smoke, CPU)

Configs in `rageval/benchmark/suite.py` and `configs/`:

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
- **benchmark v1**: not built yet (Phase 2 remainder).

## Analysis plan

1. Per-config means of retrieval and claim metrics on the same items.
2. Do not run significance tests on \(n=8\) as confirmatory results.
3. Qualitative cases: mixed-support, unanswerable, conflicting.
4. Report generator blinding (RQ4) as an engineering check on the mock.

## Exclusions

No paid API runs unless separately approved. No silent model fallback.
