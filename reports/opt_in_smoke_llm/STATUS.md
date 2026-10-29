# Opt-in live LLM smoke — not run

**Date:** 2026-10-29  
**Software:** RAGeval 0.2.1  
**Config:** `configs/opt_in/smoke_llm.yaml` (`opt_in: true`, OpenAI-compatible HTTP on `smoke_v1`)

A live LLM generator was **not** executed in this increment.

| Check | Result |
| --- | --- |
| `OPENAI_API_KEY` / `RAGEVAL_API_KEY` | unset |
| Ollama `http://127.0.0.1:11434` | process up; `{"models":[]}` |
| Hugging Face cache causal LM | MiniLM / DeBERTa NLI / ms-marco reranker / kokoro-onnx only |

What was **not** done:

- No call to OpenAI, Ollama, or `local_hf`.
- No substitution of `MockGenerator` for a missing LLM.
- No silent NLI→heuristic fallback.
- No scores copied onto this config.

How to run it later (CLI only; HTTP jobs refuse opt-in):

```bash
export OPENAI_API_KEY=...   # or point pipeline_paths at ollama_http.yaml / local_hf.yaml
rageval experiment --config configs/opt_in/smoke_llm.yaml --allow-opt-in --output-dir experiments/runs
```

Official published tables remain blinded-mock run `20261028T183042Z_a97ad68f`. Companion mock+NLI remains `20261029T165024Z_657c8089`.
