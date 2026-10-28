# Related work (short note)

RAGeval is an evaluation *framework and (planned) benchmark*. Claim-level RAG evaluation already exists. This file records overlap so later papers do not over-claim novelty.

## Name disambiguation

**RAGTruth** (Niu et al., 2024, “RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models”) is a published word- and span-level hallucination corpus for RAG. This repository is **RAGeval**. It is a separate codebase and does not redistribute that corpus.

## Adjacent evaluation lines

- **RAGAS** (Es et al., 2023): automated RAG metrics, often LLM-as-judge faithfulness.
- **FActScore** (Min et al., 2023): atomic facts vs Wikipedia for long-form generation.
- **ALCE / attributed QA** (Gao et al.): citation quality for attributed generation.
- **MiniCheck, AlignScore, SummaC, TRUE**: NLI-style factual consistency.
- **CRAG, RGB, FreshQA**: RAG robustness, recency, and retrieval stress tests.

RAGeval’s intended contribution, if later results support it, is a **controlled mixed-support + conflict/unanswerable** protocol with traceable claim-to-span records and a comparison of claim-level vs answer-level scores—not the invention of claim decomposition or NLI faithfulness.
