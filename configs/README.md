# Pipeline configs

YAML maps onto `PipelineConfig` (`rageval/core/config.py`).

- `smoke_dense_256.yaml` — CI-oriented dense baseline.
- `smoke_heuristic_eval.yaml` — NLI replaced by the lexical heuristic (tests / debugging only).
- `ablation/` — the six-config matrix. `hybrid_rrf_reranked.yaml` is heavier: it loads a cross-encoder on top of MiniLM and DeBERTa.
- `experiments/` — Phase 7 named slices A–G. See `configs/experiments/README.md`.

```bash
rageval benchmark --dataset smoke_v1 --config configs/ablation/sparse_bm25_256.yaml
rageval experiment --config configs/experiments/C_retrieve.yaml
rageval report --metrics experiments/runs/<id>/metrics.json
```
