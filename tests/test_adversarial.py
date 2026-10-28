"""Unit tests for adversarial evaluations: unanswerable queries and conflicting contexts."""

from rageval.core.schemas import BenchmarkItem, TestType, Chunk, RetrievedChunk
from rageval.evaluator.evaluator import RAGEvalEvaluator


def test_unanswerable_abstention():
    evaluator = RAGEvalEvaluator()
    item = BenchmarkItem(
        id="adv_unans",
        question="What is the Japanese market share of ApexCloud?",
        test_type=TestType.UNANSWERABLE,
        expected_abstention=True,
    )

    # 1. Model correctly abstaining
    ans_abstain = "I do not have sufficient information in the provided context to answer this question."
    res_abstain = evaluator.evaluate_query(
        question=item.question,
        generated_answer=ans_abstain,
        retrieved_chunks=[],
        item=item,
    )
    assert res_abstain.abstained is True
    assert res_abstain.correctly_abstained is True

    # 2. Model hallucinating instead of abstaining
    ans_hallucinate = "ApexCloud held 45% of the Japanese cloud market in 2024."
    res_hallucinate = evaluator.evaluate_query(
        question=item.question,
        generated_answer=ans_hallucinate,
        retrieved_chunks=[],
        item=item,
    )
    assert res_hallucinate.abstained is False
    assert res_hallucinate.correctly_abstained is False
    assert res_hallucinate.hallucination_rate == 1.0
