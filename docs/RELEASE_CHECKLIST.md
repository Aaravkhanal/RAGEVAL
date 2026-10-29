# Release checklist

Use before tagging. Version on this branch: **0.2.0rc1** (tag `v0.2.0-rc1`).

- [ ] `pyproject.toml` version matches `rageval/__init__.py`
- [ ] `LICENSE` (MIT) and `data/LICENSE.md` present
- [ ] `pip install --require-hashes -r requirements-lock-fast.txt && pip install --no-deps -e .` in a clean extra-env
- [ ] Locks regenerated with `bash scripts/compile_locks.sh` after extra changes; all-lock still `torch==…+cpu`
- [ ] `pytest -m "not hf"` passes
- [ ] `python -m rageval.cli experiment --config configs/experiments/smoke.yaml --max-items 2` writes `metrics.json`
- [ ] `python -m rageval.cli evaluate --method heuristic --question ...` does not download models
- [ ] Committed `reports/phase7/v1_matrix/metrics.json` matches FINDINGS / paper.tex (no canned 16.4%)
- [ ] No API keys or `.env` files in git (`pytest tests/test_release.py`)
- [ ] Generator YAML has no `api_key` field; openai/ollama/local_hf tests use mocks/stubs only
- [ ] README extras and corpus description match `data/cards/`
- [ ] `POST /benchmark/run` is 410; evaluate-on-context stays sync
- [ ] `POST /experiments` with `config=smoke` returns 202; poll `GET /experiments/{id}` until complete; unknown names 400; heavy without `allow_heavy` 403; second job 409
- [x] `gh workflow run nightly.yml` (or Actions → RAGeval slow tests) is green; URL recorded in `docs/REPRODUCIBILITY.md` ([run 40891849818](https://github.com/Aaravkhanal/RAGEVAL/actions/runs/40891849818))
- [ ] Tag annotated `v0.2.0-rc1`; do not claim SOTA or confirmatory RAG rankings
