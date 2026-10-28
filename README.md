# RAGTruth: Research-Grade RAG Faithfulness & Claim Attribution Benchmark

> A scientific evaluation and benchmarking framework for detecting unreliable AI answers, hallucinated statements, and citation misattributions in Retrieval-Augmented Generation (RAG) applications.

---

## 🌟 Standout Twist: Atomic Claim-Level Verification

Conventional RAG evaluations produce a single, vague binary score for an entire response (e.g. "answer is 70% helpful"). This fails to pinpoint *which* specific sentence or proposition is an unsupported fabrication or a direct contradiction.

**RAGTruth** decomposes answers into fine-grained atomic propositions and evaluates them against retrieved context using Natural Language Inference (NLI):
- **Entailment (Supported)**: The claim is strictly supported by source evidence.
- **Contradiction (Factual Conflict)**: The claim directly contradicts retrieved facts.
- **Neutral (Hallucination / Unsupported)**: The claim is extrapolated or fabricated without supporting evidence in the corpus.

In addition, RAGTruth audits **Citation Precision and Recall**, flagging hallucinated references (citing non-existent chunk tags) and missing citations.

---

## 🚀 Key Features
1. **Curated Multi-Domain Benchmark**: Finance (10-Q SEC reports), Biomedical clinical trials (NEJM), and Distributed Systems (OSDI).
2. **Adversarial Test Suite**: Conflicting document pairs (temporal or source conflict) and unanswerable questions measuring model abstention accuracy.
3. **Combinatorial Ablation Matrix**:
   - Chunk sizes: 128, 256, 512 tokens.
   - Retrieval models: Dense FAISS cosine search (`sentence-transformers/all-MiniLM-L6-v2`), BM25 lexical search, and Hybrid Reciprocal Rank Fusion (RRF).
   - Neural Cross-Encoder Rerankers (`cross-encoder/ms-marco-MiniLM-L-6-v2`).
4. **Metrics**:
   - Retrieval: Recall@1, Recall@3, Recall@5, MRR, NDCG@k, Noise Ratio.
   - Generation: Claim Faithfulness Rate, Hallucination Rate, Contradiction Rate, Citation Precision, Citation Recall.
   - Efficiency: Latency profiling (mean & p95 ms) and estimated inference cost.
5. **Research Paper Analysis & Visualizations**:
   - Automated Pareto frontier curves (Latency vs. Faithfulness).
   - Publication-ready LaTeX tables (`\begin{table}`) and Markdown empirical reports.
6. **FastAPI Service & Web Dashboard**: Interactive real-time UI for claim auditing and benchmark inspection.

---

## 🛠️ Quickstart

### 1. Installation
```bash
pip install -e .
```

### 2. Run the Benchmark Suite
```bash
ragtruth benchmark --data-dir data --output-dir reports
```

### 3. Generate Paper Analysis & Scientific Figures
```bash
ragtruth report --output-dir reports
```
This produces:
- `reports/paper_analysis.md`
- `reports/benchmark_summary.csv`
- `reports/benchmark_table.tex`
- `reports/figures/fig1_pareto_latency_faithfulness.png`
- `reports/figures/fig2_claim_attribution_breakdown.png`
- `reports/figures/fig3_retrieval_recall_mrr.png`
- `reports/figures/fig4_adversarial_abstention.png`

### 4. Launch the Interactive Dashboard
```bash
ragtruth serve --port 8000
```
Open your browser to `http://localhost:8000` to interactively audit claims with visual green/yellow/red status pills.

### 5. Run Unit Tests
```bash
pytest -v
```
