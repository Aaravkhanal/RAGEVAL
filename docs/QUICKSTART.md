# Quickstart

RAGeval is an installable Python package (`rageval`). It is **not** Niu et al. (2024) RAGTruth.

## Fast path (no Hugging Face models)

```bash
python -m pip install -e ".[dev,api]"
pytest -m "not hf"
python -m rageval.cli evaluate --method heuristic \
  --question "What is the test question?" \
  --answer "The test is valid [1]." \
  --context "The test is valid."
python -m rageval.cli experiment \
  --config configs/experiments/smoke.yaml \
  --output-dir experiments/runs
```

The smoke experiment uses BM25 + a blinded mock generator + a lexical heuristic. It is a CI fixture, not a publication result.

## Research path (MiniLM, DeBERTa, FAISS)

```bash
python -m pip install -e ".[all]"
pytest
python -m rageval.cli validate --dataset benchmark_v1
python -m rageval.cli report --metrics reports/phase7/v1_matrix/metrics.json --output-dir /tmp/rageval-report
```

First NLI/embedding calls download Hugging Face weights unless they are already cached. Official generation is a blinded mock. Opt-in LLM backends (`configs/opt_in/`) read `OPENAI_API_KEY` or `RAGEVAL_API_KEY` from the environment; HTTP errors raise instead of becoming the answer.

## Read a completed run

```bash
python -m rageval.cli findings \
  --metrics reports/phase7/v1_matrix/metrics.json \
  --output-dir /tmp/findings \
  --run-id 20261028T183042Z_a97ad68f
python -m rageval.cli serve --port 8000
```

`GET /datasets` and `GET /experiments` list completed runs. `POST /experiments` with `{"config": "smoke", "max_items": 2}` returns 202 and writes `experiments/runs/<id>/`. Heavy NLI configs need `"allow_heavy": true`. `POST /benchmark/run` stays 410. Live `POST /evaluate/answer` stays sync.

## Extras

| Extra | What it adds |
| --- | --- |
| (none) | Schemas, metrics, BM25, YAML, findings tables |
| `dev` | pytest |
| `api` | FastAPI dashboard |
| `viz` | matplotlib figures |
| `bench` | torch, transformers, sentence-transformers, faiss-cpu, httpx |
| `all` | research install |

See `docs/REPRODUCIBILITY.md` and `docs/RELEASE_CHECKLIST.md`.
