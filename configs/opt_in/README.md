# Opt-in generator backends

These YAML files are **not** part of the official ablation or HTTP job allowlist (`configs/experiments/`). They document how to point RAGeval at a real LLM.

```bash
cp .env.example .env   # gitignored; never commit secrets
# NVIDIA NIM (OpenAI-compatible):
#   NVIDIA_API_KEY=nvapi-...
rageval experiment --config configs/opt_in/smoke_llm_nvidia.yaml --allow-opt-in --output-dir experiments/runs
rageval experiment --config configs/opt_in/benchmark_llm_nvidia.yaml --allow-opt-in --output-dir experiments/runs
# OpenAI / Ollama / local_hf:
rageval experiment --config configs/opt_in/smoke_llm.yaml --allow-opt-in --output-dir experiments/runs
```

- Keys come from `NVIDIA_API_KEY`, `OPENAI_API_KEY`, or `RAGEVAL_API_KEY` (or `GeneratorConfig.api_key_env`). There is no `api_key` field on `GeneratorConfig`.
- CLI `main()` loads a gitignored `.env` from cwd or the repo root. HTTP jobs still refuse `opt_in: true`.
- HTTP errors raise `RuntimeError`. They are not returned as the model answer.
- NVIDIA reasoning models may put text in `reasoning_content` when `content` is empty; the OpenAI-like generator accepts that.
- `local_hf` needs `pip install -e ".[bench]"`. A missing model does not fall back to the mock generator.
- `estimated_cost_usd` stays null unless `evaluator.pricing_source` and both USD/million prices are set.
- Official published tables remain blinded-mock run `20261028T183042Z_a97ad68f`.
- CLI requires `--allow-opt-in`. HTTP jobs never list `configs/opt_in/` and refuse `opt_in: true` even if a file is copied into `configs/experiments/`.
- Live NVIDIA NIM smoke on `smoke_v1`: run `20261030T052448Z_6df3afb9`. Sparse companion on `benchmark_v1` 1.2.0: `20261030T052638Z_79a8b21d` (`reports/phase7/nvidia_nim_v1/`). Dense+hybrid: `configs/opt_in/benchmark_llm_nvidia_retrieve.yaml`. Model `nvidia/nemotron-3.5-bolt-e4b`. Do not treat those as the published ablation.
