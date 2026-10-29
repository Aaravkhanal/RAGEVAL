# Release checklist

Use before tagging. Version on this branch: **0.2.0** (tag `v0.2.0`). This is a **software** release. Official ablation tables remain blinded-mock run `20261028T183042Z_a97ad68f`. Do not claim SOTA or confirmatory RAG rankings.

- [x] `pyproject.toml` version matches `rageval/__init__.py` (and FastAPI `app.version`)
- [x] `LICENSE` (MIT) and `data/LICENSE.md` present
- [x] `CHANGELOG.md` (Keep a Changelog) records 0.2.0rc1 → 0.2.0 and the recorded-run banner
- [x] Fast GitHub CI installs `requirements-lock-fast.txt` with `--require-hashes` then `pip install --no-deps -e .`
- [x] Locks last compiled with `bash scripts/compile_locks.sh`; all-lock still `torch==…+cpu` (P3; no extra changes in this tag)
- [x] `pytest -m "not hf"` (run locally before tag; GitHub `ci.yml` on the tag commit)
- [x] `python -m rageval.cli experiment --config configs/experiments/smoke.yaml --max-items 2` writes `metrics.json` (P1 job tests plus CLI smoke)
- [x] `python -m rageval.cli evaluate --method heuristic --question ...` does not download models
- [x] Committed `reports/phase7/v1_matrix/metrics.json` matches FINDINGS / paper.tex (no canned 16.4%)
- [x] No API keys or `.env` files in git (`pytest tests/test_release.py`)
- [x] Generator YAML has no `api_key` field; openai/ollama/local_hf tests use mocks/stubs only
- [x] README extras and corpus description match `data/cards/`
- [x] `POST /benchmark/run` is 410; evaluate-on-context stays sync
- [x] `POST /experiments` with `config=smoke` returns 202; poll `GET /experiments/{id}` until complete; unknown names 400; heavy without `allow_heavy` 403; second job 409
- [x] Hugging Face nightly is green; URL in `docs/REPRODUCIBILITY.md` ([run 40891849818](https://github.com/Aaravkhanal/RAGEVAL/actions/runs/40891849818))
- [x] `python -m build && twine check dist/*` locally (sdist + wheel)
- [ ] `twine upload dist/*` — **maintainer only**, needs a PyPI token. Not run in CI. Do not treat the GitHub tag as a PyPI publish.
- [x] Annotated tag `v0.2.0`; Docker image tag `rageval:0.2.0`

Rebuild a local wheel after extras change; regenerate locks first.

```bash
python -m pip install build twine
python -m build
twine check dist/*
# Maintainer, after GitHub tag is pushed:
# twine upload dist/*
```
