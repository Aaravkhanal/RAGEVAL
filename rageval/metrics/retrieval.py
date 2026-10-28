"""Retrieval metric formulas. Relevance is document-id membership unless noted."""

from __future__ import annotations

import math
from typing import Iterable, Sequence, Set


def _as_list(ids: Iterable[str]) -> list[str]:
    return [str(x) for x in ids]


def recall_at_k(retrieved_ids: Sequence[str], gold_ids: Set[str], k: int) -> float:
    """|unique gold ids in retrieved[:k]| / |gold ids|. Empty gold → 0.0."""
    if k <= 0 or not gold_ids:
        return 0.0
    hits = set(_as_list(retrieved_ids)[:k]) & set(gold_ids)
    return len(hits) / len(gold_ids)


def mrr(retrieved_ids: Sequence[str], gold_ids: Set[str]) -> float:
    """Reciprocal rank of the first retrieved gold document. 0 if none."""
    if not gold_ids:
        return 0.0
    for rank, doc_id in enumerate(_as_list(retrieved_ids), start=1):
        if doc_id in gold_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved_ids: Sequence[str], gold_ids: Set[str], k: int) -> float:
    """Binary-relevance nDCG@k at document level."""
    if k <= 0 or not gold_ids:
        return 0.0
    dcg = 0.0
    for rank, doc_id in enumerate(_as_list(retrieved_ids)[:k], start=1):
        rel = 1.0 if doc_id in gold_ids else 0.0
        dcg += rel / math.log2(rank + 1)
    ideal_hits = min(len(gold_ids), k)
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, ideal_hits + 1))
    return (dcg / idcg) if idcg > 0 else 0.0


def noise_ratio(retrieved_ids: Sequence[str], gold_ids: Set[str], k: int) -> float:
    """Fraction of retrieved[:k] documents that are not gold. Empty retrieve → 0."""
    ids = _as_list(retrieved_ids)[:k]
    if not ids:
        return 0.0
    relevant = sum(1 for doc_id in ids if doc_id in gold_ids)
    return 1.0 - (relevant / len(ids))
