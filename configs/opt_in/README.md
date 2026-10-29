# Opt-in generator backends

These YAML files are **not** part of the official ablation or HTTP job allowlist (`configs/experiments/`). They document how to point RAGeval at a real LLM.

```bash
export OPENAI_API_KEY=...   # openai backend; never commit this
rageval experiment --config configs/opt_in/smoke_llm.yaml --allow-opt-in --output-dir experiments/runs
rageval benchmark --dataset smoke_v1 --config configs/opt_in/openai_http.yaml --allow-opt-in --output-dir experiments/runs
```

- Keys come from `OPENAI_API_KEY` or `RAGEVAL_API_KEY`. There is no `api_key` field on `GeneratorConfig`.
- HTTP errors raise `RuntimeError`. They are not returned as the model answer.
- `local_hf` needs `pip install -e ".[bench]"`. A missing model does not fall back to the mock generator.
- `estimated_cost_usd` stays null unless `evaluator.pricing_source` and both USD/million prices are set.
- Official published tables remain blinded-mock run `20261028T183042Z_a97ad68f`.
- CLI requires `--allow-opt-in`. HTTP jobs never list `configs/opt_in/` and refuse `opt_in: true` even if a file is copied into `configs/experiments/`.
- This environment did **not** run a live LLM smoke (no OpenAI key, empty Ollama model list, no local causal LM). See `reports/opt_in_smoke_llm/STATUS.md`. Do not treat the blinded mock as that run.
