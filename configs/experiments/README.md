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

```bash
rageval experiment --config configs/experiments/C_retrieve.yaml --dataset benchmark_v1
rageval report --metrics experiments/runs/<id>/metrics.json --output-dir reports/phase7
```

The recorded ablation in `reports/` is **v1.0.0** (16 docs, 24 items, overlap 16/32/64 on the dense chunk configs). `A_chunk.yaml` is the Phase 7 protocol with overlap fixed at 32; it has **not** been re-run on that protocol. Do not treat those YAML files as if they produced new numbers.

G is analysis-only: `rageval experiment --config configs/experiments/G_claim_vs_answer.yaml` errors until pipelines exist. Use `BenchmarkReporter.claim_vs_answer_markdown`.
