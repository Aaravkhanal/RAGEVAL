# Release checklist

Use before tagging. Version on this branch: **0.2.0rc1** (tag `v0.2.0-rc1`).

- [ ] `pyproject.toml` version matches `rageval/__init__.py`
- [ ] `LICENSE` (MIT) and `data/LICENSE.md` present
- [ ] `pip install -e ".[dev,api]"` in a clean extra-env
- [ ] `pytest -m "not hf"` passes
- [ ] `python -m rageval.cli experiment --config configs/experiments/smoke.yaml --max-items 2` writes `metrics.json`
- [ ] `python -m rageval.cli evaluate --method heuristic --question ...` does not download models
- [ ] Committed `reports/phase7/v1_matrix/metrics.json` matches FINDINGS / paper.tex (no canned 16.4%)
- [ ] No API keys or `.env` files in git (`pytest tests/test_release.py`)
- [ ] README extras and corpus description match `data/cards/`
- [ ] `POST /benchmark/run` is 410; evaluate-on-context stays sync
- [ ] Tag annotated `v0.2.0-rc1`; do not claim SOTA or confirmatory RAG rankings
