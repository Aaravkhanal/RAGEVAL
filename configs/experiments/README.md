# Phase 7 experiment slices

Named YAML under this directory. `label` is `v1` or `pilot`.

| File | Family | Pipelines |
| --- | --- | --- |
| `A_chunk.yaml` | chunk | dense MiniLM, overlap **fixed at 32**, sizes 128/256/512 |
| `B_embed.yaml` | embed | MiniLM only. Other embedders listed as `opt_in_embedders` and are not run |
| `C_retrieve.yaml` | retrieve | dense vs BM25 vs hybrid at chunk 256 |
| `D_rerank.yaml` | rerank | hybrid rerank off vs on |
| `E_verifier.yaml` | verifier | DeBERTa NLI vs lexical heuristic (diagnostic) |
| `F_ablate.yaml` | ablate | sparse / dense / hybrid+rerank |
| `G_claim_vs_answer.yaml` | analysis | no pipelines; table from `metrics.json` mixed-support slice |
| `smoke.yaml` | smoke | BM25 + lexical heuristic on `smoke_v1` (CI; not a publication result) |
| `H_independent.yaml` | independent | companion slice: one item per unused gold document on `benchmark_v1` 1.4.0 (n=30, single-author; not a replacement for `a97ad68f`) |

```bash
rageval experiment --config configs/experiments/smoke.yaml
rageval experiment --config configs/experiments/C_retrieve.yaml
rageval report --metrics experiments/runs/<id>/metrics.json --output-dir reports/phase7
```

The published ablation in `reports/phase7/v1_matrix/` is **v1.0.0** (16 docs, 24 items, overlap 16/32/64 on the dense chunk configs). Companion **v1.1.0** (`v1_1_matrix/`) and **v1.2.0** (`v1_2_matrix/`) tables use the same six-config matrix. `A_chunk.yaml` is the Phase 7 protocol with overlap fixed at 32; its snapshot is `reports/phase7/A_chunk_overlap32/`. Do not treat the six-config YAML files as if they produced those overlap-32 numbers.

G is analysis-only: `rageval experiment --config configs/experiments/G_claim_vs_answer.yaml` errors until pipelines exist. Use `BenchmarkReporter.claim_vs_answer_markdown`.
