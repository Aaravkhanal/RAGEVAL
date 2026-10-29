"""Phase 6: reviewed scenarios, paired loader, taxonomy, robustness slices."""

from rageval.analysis.failure_taxonomy import (
    REQUIRED_REVIEWED_SCENARIOS,
    TAXONOMY_STAGES,
    apply_retrieval_protocol,
    attribute_failure,
)
from rageval.core.schemas import (
    BenchmarkItem,
    CitationMetric,
    QueryEvaluationResult,
    RetrievalMetrics,
    RetrievedChunk,
    TestType,
)
from rageval.dataset.benchmark_v1 import DATASET_ID
from rageval.dataset.loader import DatasetLoader
from rageval.metrics.aggregate import robustness_by_scenario_type, summarize_results


def _result(**kwargs) -> QueryEvaluationResult:
    defaults = dict(
        query_id="q",
        question="Q",
        test_type=TestType.STANDARD,
        generated_answer="A",
        faithfulness_score=1.0,
        hallucination_rate=0.0,
        contradiction_rate=0.0,
        citation_metrics=CitationMetric(
            total_citations=0,
            valid_citations=0,
            citation_precision=1.0,
            citation_recall=1.0,
            citation_support_precision=1.0,
        ),
        retrieval_metrics=RetrievalMetrics(recall_at_5=1.0, mrr=1.0, retrieved_count=1),
    )
    defaults.update(kwargs)
    return QueryEvaluationResult(**defaults)


def test_reviewed_scenarios_and_paired_loader():
    loader = DatasetLoader("data", dataset_id=DATASET_ID)
    items = loader.load_benchmark("all")
    reviewed = {item.scenario_type for item in items if item.reviewed}
    for scenario in REQUIRED_REVIEWED_SCENARIOS:
        assert scenario in reviewed, scenario

    pairs = loader.load_paired_items()
    assert "pair_harbornet_q2" in pairs
    pair = pairs["pair_harbornet_q2"]
    assert pair.is_complete()
    assert pair.same_question()
    assert pair.control.id == "v1_007"
    assert pair.with_conflict.id == "v1_028"
    assert pair.with_conflict.scenario_type == "conflicting"


def test_empty_context_protocol_drops_retrieval():
    item = BenchmarkItem(
        id="e",
        question="Kael-9?",
        test_type=TestType.UNANSWERABLE,
        expected_abstention=True,
        scenario_type="empty_context",
    )
    from rageval.core.schemas import Chunk

    chunks = [
        RetrievedChunk(
            chunk=Chunk(
                id="c",
                doc_id="d",
                text="noise",
                chunk_index=0,
                token_count=1,
                start_char=0,
                end_char=5,
            ),
            score=1.0,
            rank=1,
        )
    ]
    assert apply_retrieval_protocol(item, chunks) == []
    other = BenchmarkItem(id="s", question="q", scenario_type="standard")
    assert apply_retrieval_protocol(other, chunks) == chunks


def test_taxonomy_tagging_and_attribution():
    assert "generation" in TAXONOMY_STAGES
    unans = _result(
        query_id="v1_013",
        test_type=TestType.UNANSWERABLE,
        scenario_type="unanswerable",
        generated_answer="The Eagle landed in the Sea of Tranquility.",
        faithfulness_score=0.5,
        hallucination_rate=0.0,
        contradiction_rate=0.5,
        abstained=False,
        correctly_abstained=False,
        retrieval_metrics=RetrievalMetrics(recall_at_5=0.0, mrr=0.0, retrieved_count=5),
    )
    tagged = attribute_failure(unans)
    assert tagged["has_failure"] is True
    assert tagged["primary_stage"] in TAXONOMY_STAGES
    assert "retrieval" in tagged["stages"]
    assert "generation" in tagged["stages"]

    mixed = _result(
        query_id="v1_019",
        scenario_type="mixed_support",
        answer_f1=0.66,
        faithfulness_score=0.5,
        hallucination_rate=0.0,
        contradiction_rate=0.5,
        generated_answer="Influenza A and B cause seasonal epidemics.",
        retrieval_metrics=RetrievalMetrics(recall_at_5=1.0, mrr=1.0, retrieved_count=5),
    )
    mixed_tag = attribute_failure(mixed)
    assert mixed_tag["primary_stage"] == "generation"


def test_robustness_by_scenario_type():
    rows = [
        _result(query_id="a", scenario_type="unanswerable", faithfulness_score=0.0, test_type=TestType.UNANSWERABLE, abstained=False),
        _result(query_id="b", scenario_type="unanswerable", faithfulness_score=0.5, test_type=TestType.UNANSWERABLE, abstained=False),
        _result(query_id="c", scenario_type="standard", faithfulness_score=1.0),
    ]
    sliced = robustness_by_scenario_type(rows)
    assert sliced["unanswerable"]["n"] == 2
    assert sliced["unanswerable"]["claim_support_rate"] == 0.25
    assert sliced["standard"]["n"] == 1
    summary = summarize_results(rows)
    assert summary["overall_score"] is None
    assert "by_scenario" not in summary
