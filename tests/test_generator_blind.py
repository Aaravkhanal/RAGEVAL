"""Mock generator must not use gold test_type / expected_abstention."""

import inspect

from rageval.core.schemas import BenchmarkItem, Chunk, RetrievedChunk, TestType
from rageval.pipeline.generator import MockGenerator, OpenAILikeGenerator


def _chunk():
    return RetrievedChunk(
        chunk=Chunk(
            id="c1",
            doc_id="d1",
            text="ApexCloud non-GAAP gross margin expanded to 78.2% in Q3 2024.",
            chunk_index=0,
            token_count=10,
            start_char=0,
            end_char=60,
        ),
        score=1.0,
        rank=1,
    )


def test_unanswerable_item_does_not_force_abstention_when_context_exists():
    item = BenchmarkItem(
        id="u1",
        question="What is the Japanese revenue share?",
        test_type=TestType.UNANSWERABLE,
        expected_abstention=True,
    )
    gen = MockGenerator(mode="faithful", abstention_policy="empty_context")
    answer, _, _ = gen.generate(item.question, [_chunk()], item=item)
    assert "do not have sufficient information" not in answer.lower()
    assert "78.2%" in answer


def test_empty_context_abstains():
    gen = MockGenerator(mode="faithful", abstention_policy="empty_context")
    answer, _, _ = gen.generate("Any question?", [], item=None)
    assert "do not have sufficient information" in answer.lower()


def test_generator_source_does_not_read_test_type():
    for cls in (MockGenerator, OpenAILikeGenerator):
        src = inspect.getsource(cls.generate)
        assert "test_type" not in src
        assert "expected_abstention" not in src
        assert "gold_answer" not in src
        assert "scenario_type" not in src


def test_poisoned_gold_answer_is_not_copied():
    item = BenchmarkItem(
        id="leak",
        question="What is monthly churn?",
        gold_answer="LEAKED_GOLD_ANSWER_TOKEN",
        test_type=TestType.UNANSWERABLE,
        expected_abstention=True,
        scenario_type="unanswerable",
    )
    gen = MockGenerator(mode="faithful", abstention_policy="empty_context")
    answer, _, _ = gen.generate(item.question, [_chunk()], item=item)
    assert "LEAKED_GOLD_ANSWER_TOKEN" not in answer
    assert "do not have sufficient information" not in answer.lower()
