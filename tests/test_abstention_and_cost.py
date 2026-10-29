"""Abstention accuracy and null cost without a pricing source."""

from rageval.core.config import EvaluatorConfig
from rageval.evaluator.evaluator import RAGEvalEvaluator
from rageval.metrics.abstention import abstention_accuracy
from rageval.metrics.system import estimated_cost_usd


def test_abstention_accuracy_unanswerable_only():
    # two unanswerable: one abstain, one not; one answerable abstain ignored
    assert abstention_accuracy([True, False, True], [True, True, False]) == 0.5
    assert abstention_accuracy([False], [False]) == 1.0


def test_cost_null_without_pricing_source():
    cost, source = estimated_cost_usd(100, 50, 1.0, 2.0, None)
    assert cost is None and source is None
    cost, source = estimated_cost_usd(1_000_000, 1_000_000, 1.0, 2.0, "vendor-list-2026-10-29")
    assert cost == 3.0
    assert source == "vendor-list-2026-10-29"


def test_live_evaluate_cost_is_null_by_default():
    evaluator = RAGEvalEvaluator(EvaluatorConfig(method="heuristic"))
    result = evaluator.evaluate_query(
        question="Q",
        generated_answer="I do not have sufficient information in the provided context to answer.",
        retrieved_chunks=[],
    )
    assert result.estimated_cost_usd is None
    assert result.cost_pricing_source is None
