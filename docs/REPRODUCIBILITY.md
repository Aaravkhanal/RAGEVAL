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

Current `benchmark_v1` on disk is **1.1.0** (18/28). Companion mock+NLI tables: `reports/phase7/v1_1_matrix/` from run `20261029T165024Z_657c8089`. Do not copy 1.0.0 scores onto `v1_025`–`v1_028`. The published table remains `a97ad68f`.

To regenerate tables **from the committed JSON** (no model load):

```bash
python -m rageval.cli report \
  --metrics reports/phase7/v1_matrix/metrics.json \
  --output-dir /tmp/rageval-report
```

Re-running the six-config NLI matrix is optional, CPU-heavy, and **not** required to check that reports match the run. If you re-run, write a new `experiments/runs/<id>/` folder. Completed runs refuse to overwrite `metrics.json`.

## Pinned install

Loose extras stay in `pyproject.toml`. Committed hashed locks:

| File | Extra | Target |
| --- | --- | --- |
| `requirements-lock-fast.txt` | `[dev,api]` | universal wheels, Python ≥3.10 (fast CI) |
| `requirements-lock-all.txt` | `[all]` | **manylinux x86_64**, Python 3.12, **CPU** torch + `faiss-cpu` (Docker / weekly HF job) |

```bash
python -m pip install --upgrade pip setuptools wheel
pip install --require-hashes -r requirements-lock-fast.txt
pip install --no-deps -e .
pytest -m "not hf"
```

Regenerate locks after changing extras:

```bash
bash scripts/compile_locks.sh
```

That script uses `uv pip compile` (`uv` 0.13+). The all-lock sets `--extra-index-url https://download.pytorch.org/whl/cpu` so `torch==…+cpu` is fetchable. It is **not** a CUDA image and is **not** bit-for-bit NLI logits across machines.

## Docker

```bash
docker build --platform linux/amd64 -t rageval:0.2.1 .
docker run --rm -p 8000:8000 rageval:0.2.1
```

`--platform linux/amd64` is required on Apple Silicon because the all-lock is x86_64. Default `CMD` is `rageval serve`. Hugging Face weights are **not** in the image; first NLI/embed call still downloads them.

This job is not in GitHub Actions (torch wheels blow the fast-CI minute budget).

## Software package (0.2.1)

Git tag `v0.2.1` is the current software release (dashboard job UI on top of `v0.2.0`). It does **not** upload to PyPI. Official tables remain run `20261028T183042Z_a97ad68f`.

```bash
python -m pip install build twine
python -m build
twine check dist/*
# Maintainer only (PyPI token; not CI):
# twine upload dist/*
```

## Hugging Face CI

Fast CI is `pytest -m "not hf"`. The slow job is `.github/workflows/nightly.yml` (Python 3.12, hashed `requirements-lock-all.txt`, CPU torch). It caches `${{ github.workspace }}/.cache/huggingface` keyed on `pyproject.toml`, the all-lock, and the workflow file. NLI tests and embed/FAISS tests run as **separate pytest processes** so DeBERTa and MiniLM do not sit in RAM together. There is **no** `continue-on-error`.

```bash
gh workflow run nightly.yml --repo Aaravkhanal/RAGEVAL
# Actions tab: https://github.com/Aaravkhanal/RAGEVAL/actions/workflows/nightly.yml
```

First proven green run: [40891849818](https://github.com/Aaravkhanal/RAGEVAL/actions/runs/40891849818) (`workflow_dispatch`, commit `94c9eeb`, 2026-10-29). Python 3.12, hashed `requirements-lock-all.txt`, CPU torch. NLI/evaluator: 8 passed, 122 deselected in 29 s. Embed/FAISS: 2 passed in 9 s. Hub cache saved (~757 MB) for later weekly runs.

## Smoke (CI / extra-env)

```bash
python -m pip install --require-hashes -r requirements-lock-fast.txt
python -m pip install --no-deps -e .
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
