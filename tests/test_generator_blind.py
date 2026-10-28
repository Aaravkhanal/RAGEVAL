"""Mock generator must not use gold test_type / expected_abstention."""

from rageval.core.schemas import BenchmarkItem, Chunk, RetrievedChunk, TestType
from rageval.pipeline.generator import MockGenerator


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
