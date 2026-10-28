"""Unit tests for retrieval metric formulas."""

import pytest

from rageval.metrics.retrieval import mrr, ndcg_at_k, noise_ratio, recall_at_k


def test_recall_mrr_ndcg_hand_computed():
    retrieved = ["d1", "d9", "d2"]
    gold = {"d1", "d2"}
    assert recall_at_k(retrieved, gold, 1) == 0.5
    assert recall_at_k(retrieved, gold, 3) == 1.0
    assert mrr(retrieved, gold) == 1.0
    assert noise_ratio(retrieved, gold, 3) == pytest.approx(1.0 / 3.0)
    ndcg = ndcg_at_k(retrieved, gold, 3)
    assert 0.0 < ndcg <= 1.0


def test_empty_gold_pure_function_is_zero():
    assert recall_at_k(["d1"], set(), 5) == 0.0
    assert mrr(["d1"], set()) == 0.0
