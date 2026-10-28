# RAGeval research specification

**Status:** Phase 1 draft, frozen for the smoke-scale implementation that follows.  
**Hypothesis, not a result:** claim-level evidence verification can expose mixed-quality RAG answers that answer-level scores treat as uniformly good.

This project does **not** claim that claim-level evaluation is novel. See `RELATED_WORK.md`.

## Research questions

**RQ1.** How do chunk size, retrieval family (dense / BM25 / hybrid), and reranking affect document-level Recall@k / MRR and claim-support rates on a frozen set?

**RQ2.** How accurately can an automated verifier classify claims as supported, partially supported, unsupported, contradicted, or ambiguous relative to gold labels (per-class P/R/F1 and macro-F1)?

**RQ3.** Do claim-level rates identify mixed-support answers that an answer-level metric (token F1 or whole-answer NLI) marks as correct?

**RQ4.** When the generator cannot see gold answerability labels, how do pipelines behave on unanswerable and conflicting items (abstention accuracy, contradiction rate, hedge language)?

**RQ5.** What latency (and optional priced cost) trade-offs accompany the baseline configs?

Core for the current codebase: RQ2–RQ4 on the smoke set (engineering validation) and on benchmark v1 once it exists. RQ1 and RQ5 are reported only when retrieval metrics actually move.

## Hypotheses (falsifiable)

| RQ | Hypothesis | Falsified if |
| --- | --- | --- |
| RQ1 | Hybrid RRF improves Recall@5 vs dense-only on the frozen set. | Recall@5 is equal within sampling noise. |
| RQ2 | DeBERTa NLI macro-F1 on gold claims exceeds a lexical heuristic. | Heuristic ≥ NLI on macro-F1. |
| RQ3 | Claim-level unsupported/contradiction rates rank mixed-support answers above fully supported ones more often than answer-level F1 does. | Rankings agree or answer-level is better. |
| RQ4 | Blinded generators abstain less often on unanswerable items than a leaky generator that sees `test_type`. | Abstention rates are indistinguishable. |
| RQ5 | Reranking increases latency. | Mean latency does not increase. |

## Variables

- **Independent:** chunk size, retriever method, rerank on/off, verifier method (`nli` vs `heuristic`), generator backend.
- **Dependent:** Recall@k, MRR, claim support / unsupported / contradiction rates, citation support precision, abstention accuracy, stage latency.
- **Controlled:** dataset version, embedder id, decoding temperature 0, seed, top_k (except when top_k is the IV).

## Scope

**In:** English text RAG, supplied-context faithfulness, citation markers of the form `[n]`.  
**Out:** multilingual, multimodal, training a new NLI model, world-knowledge fact checking against the web.

## Official vs diagnostic evaluation

Primary faithfulness uses **only the RAG system’s retrieved chunks**. Any extra evaluator retrieval is diagnostic and must be stored under a separate namespace.
