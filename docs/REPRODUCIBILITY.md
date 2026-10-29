# Reproducibility

How to reproduce **smoke** and the **documented v1 baseline tables**. This is not a claim that the v1 ablation is confirmatory.

## Recorded baseline (do not re-invent numbers)

| Field | Value |
| --- | --- |
| Run id | `20261028T183042Z_a97ad68f` |
| Dataset | `benchmark_v1` **1.0.0** (16 documents, 24 items) |
| Generator | blinded mock |
| Verifier | DeBERTa-v3 NLI, `allow_heuristic_fallback=false` |
| Tables | `reports/phase7/v1_matrix/metrics.json` |
| Write-up | `reports/20261028T183042Z_a97ad68f/FINDINGS.md` |
| Draft paper | `reports/paper.tex` (table matches that run; n=24 is underpowered) |

Current `benchmark_v1` on disk is **1.1.0** (18/28). Do not copy 1.0.0 scores onto `v1_025`–`v1_028`.

To regenerate tables **from the committed JSON** (no model load):

```bash
python -m rageval.cli report \
  --metrics reports/phase7/v1_matrix/metrics.json \
  --output-dir /tmp/rageval-report
```

Re-running the six-config NLI matrix is optional, CPU-heavy, and **not** required to check that reports match the run. If you re-run, write a new `experiments/runs/<id>/` folder. Completed runs refuse to overwrite `metrics.json`.

## Smoke (CI / extra-env)

```bash
python -m pip install -e ".[dev]"
python -m rageval.cli experiment --config configs/experiments/smoke.yaml --max-items 8
pytest -m "not hf"
```

`smoke_v1` is 8 synthetic documents. See `data/cards/smoke_v1.md`.

## Environment snapshot

Each `save_run` writes `manifest.json` with Python version, platform, and `git rev-parse HEAD`. The recorded ablation started from git `3f8d3a3` with uncommitted `benchmark_v1` files in the working tree; that is disclosed in `reports/README.md`.

## What is not reproduced here

- Paid LLM APIs
- A_chunk overlap-fixed-32 protocol (named YAML exists; numbers in `metrics.json` used historical overlaps 16/32/64)
- Confirmatory statistics (n=24, items share documents)
