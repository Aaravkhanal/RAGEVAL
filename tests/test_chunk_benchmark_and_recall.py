"""Chunk treatment and answerable-only retrieval metrics."""

from rageval.core.schemas import (
    BenchmarkItem,
    Chunk,
    CitationMetric,
    GoldEvidence,
    QueryEvaluationResult,
    RetrievedChunk,
    TestType,
)
from rageval.dataset.chunk_benchmark_v1 import build_benchmark
from rageval.dataset.loader import DatasetLoader
from rageval.dataset.validator import validate_benchmark_integrity
from rageval.evaluator.retrieval_metrics import RetrievalMetricsCalculator
from rageval.metrics.aggregate import summarize_results
from rageval.pipeline.chunkers import FixedTokenChunker


def test_pinned_public_documents_produce_distinct_chunk_treatments():
    built_docs, built_items = build_benchmark()
    loader = DatasetLoader("data", dataset_id="chunk_benchmark_v1")
    docs, items = loader.load_corpus(), loader.load_benchmark()
    assert [d.model_dump() for d in built_docs] == [d.model_dump() for d in docs]
    assert [i.model_dump() for i in built_items] == [i.model_dump() for i in items]
    assert validate_benchmark_integrity(docs, items, require_license=True, require_verbatim_spans=True)["valid"]
    assert min(len(doc.text.split()) for doc in docs) > 512
    counts = [len(FixedTokenChunker(size, 32).chunk_documents(docs)) for size in (128, 256, 512)]
    assert counts[0] > counts[1] > counts[2]
    assert len(items) == 30


def _retrieved(text: str, doc_id: str = "d") -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(id="c", doc_id=doc_id, text=text, chunk_index=0, token_count=len(text.split()), start_char=0, end_char=len(text)),
        score=1.0,
        rank=1,
    )


def _result(item: BenchmarkItem, retrieved: list[RetrievedChunk]) -> QueryEvaluationResult:
    return QueryEvaluationResult(
        query_id=item.id,
        question=item.question,
        test_type=item.test_type,
        generated_answer="",
        faithfulness_score=1.0,
        hallucination_rate=0.0,
        contradiction_rate=0.0,
        citation_metrics=CitationMetric(total_citations=0, valid_citations=0, citation_precision=1.0, citation_recall=1.0),
        retrieval_metrics=RetrievalMetricsCalculator.calculate(retrieved, item),
    )


def test_no_gold_is_excluded_from_recall_and_scored_separately():
    answerable = BenchmarkItem(id="a", question="Q", gold_evidence_spans=[GoldEvidence(doc_id="d", span="target fact")])
    no_answer = BenchmarkItem(id="u", question="unknown?", test_type=TestType.UNANSWERABLE, expected_abstention=True)
    answer_result = _result(answerable, [_retrieved("target fact")])
    noise_result = _result(no_answer, [_retrieved("unrelated")])
    assert answer_result.retrieval_metrics.evidence_recall_at_5 == 1.0
    assert noise_result.retrieval_metrics.no_answer_empty_retrieval is False
    metrics = summarize_results([answer_result, noise_result])
    assert metrics["recall_at_5"] == {"mean": 1.0, "n": 1}
    assert metrics["evidence_recall_at_5"] == {"mean": 1.0, "n": 1}
    assert metrics["no_answer_empty_retrieval_rate"] == {"mean": 0.0, "n": 1}
    assert summarize_results([_result(no_answer, [])])["recall_at_5"]["mean"] is None


def test_document_hit_does_not_imply_evidence_hit():
    item = BenchmarkItem(id="a", question="Q", gold_evidence_spans=[GoldEvidence(doc_id="d", span="target fact")])
    metrics = RetrievalMetricsCalculator.calculate([_retrieved("different passage")], item)
    assert metrics.recall_at_5 == 1.0
    assert metrics.evidence_recall_at_5 == 0.0
