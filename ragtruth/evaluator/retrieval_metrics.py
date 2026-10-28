"""Retrieval metric computations: Recall@k, MRR, NDCG@k, and Noise Ratio."""

from __future__ import annotations
import math
from typing import List, Set
from ragtruth.core.schemas import RetrievedChunk, BenchmarkItem, RetrievalMetrics


class RetrievalMetricsCalculator:
    """Calculates IR metrics comparing retrieved chunks against gold evidence documents."""

    @staticmethod
    def calculate(
        retrieved_chunks: List[RetrievedChunk],
        item: BenchmarkItem,
        k: int = 5,
    ) -> RetrievalMetrics:
        if not item.gold_evidence_spans:
            # If no gold evidence is expected (e.g. unanswerable questions)
            return RetrievalMetrics(
                recall_at_1=1.0 if not retrieved_chunks else 0.0,
                recall_at_3=1.0 if not retrieved_chunks else 0.0,
                recall_at_5=1.0 if not retrieved_chunks else 0.0,
                recall_at_k=1.0 if not retrieved_chunks else 0.0,
                mrr=0.0,
                ndcg_at_k=0.0,
                noise_ratio=1.0 if retrieved_chunks else 0.0,
                retrieved_count=len(retrieved_chunks),
            )

        gold_doc_ids: Set[str] = {ev.doc_id for ev in item.gold_evidence_spans if ev.doc_id}
        if not gold_doc_ids:
            return RetrievalMetrics()

        retrieved_doc_ids = [r.chunk.doc_id for r in retrieved_chunks]
        total_gold = len(gold_doc_ids)

        # Recall @ 1, 3, 5, k
        def recall_at(n: int) -> float:
            docs_at_n = set(retrieved_doc_ids[:n])
            hits = len(docs_at_n & gold_doc_ids)
            return float(hits / total_gold) if total_gold > 0 else 0.0

        r_1 = recall_at(1)
        r_3 = recall_at(3)
        r_5 = recall_at(5)
        r_k = recall_at(k)

        # MRR: reciprocal rank of the first relevant document
        mrr = 0.0
        for rank, doc_id in enumerate(retrieved_doc_ids, start=1):
            if doc_id in gold_doc_ids:
                mrr = 1.0 / rank
                break

        # NDCG@k
        dcg = 0.0
        for rank, doc_id in enumerate(retrieved_doc_ids[:k], start=1):
            rel = 1.0 if doc_id in gold_doc_ids else 0.0
            dcg += rel / math.log2(rank + 1)

        # Ideal DCG: all gold documents ranked at the very top
        idcg = sum(1.0 / math.log2(r + 1) for r in range(1, min(total_gold, k) + 1))
        ndcg = (dcg / idcg) if idcg > 0 else 0.0

        # Noise ratio: fraction of retrieved chunks that do not belong to gold documents
        relevant_chunks = sum(1 for doc_id in retrieved_doc_ids[:k] if doc_id in gold_doc_ids)
        total_eval_chunks = min(len(retrieved_doc_ids), k)
        noise_ratio = (1.0 - (relevant_chunks / total_eval_chunks)) if total_eval_chunks > 0 else 0.0

        return RetrievalMetrics(
            recall_at_1=r_1,
            recall_at_3=r_3,
            recall_at_5=r_5,
            recall_at_k=r_k,
            mrr=mrr,
            ndcg_at_k=ndcg,
            noise_ratio=noise_ratio,
            retrieved_count=len(retrieved_chunks),
        )
