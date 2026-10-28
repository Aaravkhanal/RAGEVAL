"""Retrieval metric computations: Recall@k, MRR, NDCG@k, and Noise Ratio."""

from __future__ import annotations

from typing import List, Set

from rageval.core.schemas import BenchmarkItem, RetrievedChunk, RetrievalMetrics
from rageval.metrics.retrieval import mrr as mrr_score
from rageval.metrics.retrieval import ndcg_at_k
from rageval.metrics.retrieval import noise_ratio as noise_ratio_score
from rageval.metrics.retrieval import recall_at_k


class RetrievalMetricsCalculator:
    """IR metrics comparing retrieved chunks against gold evidence documents."""

    @staticmethod
    def calculate(
        retrieved_chunks: List[RetrievedChunk],
        item: BenchmarkItem,
        k: int = 5,
    ) -> RetrievalMetrics:
        retrieved_doc_ids = [r.chunk.doc_id for r in retrieved_chunks]

        if not item.gold_evidence_spans:
            # Unanswerable / no gold passages: retrieving anything is treated as noise.
            empty = not retrieved_chunks
            return RetrievalMetrics(
                recall_at_1=1.0 if empty else 0.0,
                recall_at_3=1.0 if empty else 0.0,
                recall_at_5=1.0 if empty else 0.0,
                recall_at_k=1.0 if empty else 0.0,
                mrr=0.0,
                ndcg_at_k=0.0,
                noise_ratio=0.0 if empty else 1.0,
                retrieved_count=len(retrieved_chunks),
            )

        gold_doc_ids: Set[str] = {ev.doc_id for ev in item.gold_evidence_spans if ev.doc_id}
        if not gold_doc_ids:
            return RetrievalMetrics(retrieved_count=len(retrieved_chunks))

        return RetrievalMetrics(
            recall_at_1=recall_at_k(retrieved_doc_ids, gold_doc_ids, 1),
            recall_at_3=recall_at_k(retrieved_doc_ids, gold_doc_ids, 3),
            recall_at_5=recall_at_k(retrieved_doc_ids, gold_doc_ids, 5),
            recall_at_k=recall_at_k(retrieved_doc_ids, gold_doc_ids, k),
            mrr=mrr_score(retrieved_doc_ids, gold_doc_ids),
            ndcg_at_k=ndcg_at_k(retrieved_doc_ids, gold_doc_ids, k),
            noise_ratio=noise_ratio_score(retrieved_doc_ids, gold_doc_ids, k),
            retrieved_count=len(retrieved_chunks),
        )
