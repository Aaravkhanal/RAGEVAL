"""Check the frozen test split and its source/evidence separation."""

from rageval.dataset.benchmark_v2 import QUESTIONS, build_benchmark


def test_frozen_test_sources_and_evidence_are_disjoint():
    docs, items = build_benchmark()
    by_id = {doc.id: doc for doc in docs}
    dev_sources = {by_id[e.doc_id].source_url for item in items if item.split == "dev" for e in item.gold_evidence_spans}
    test_sources = {by_id[e.doc_id].source_url for item in items if item.split == "test" for e in item.gold_evidence_spans}
    assert dev_sources.isdisjoint(test_sources)
    assert len(test_sources) == 4
    assert len([item for item in items if item.split == "test"]) == 22
    assert len([doc for doc in docs if doc.metadata.get("synthetic")]) == 2
    for item in items:
        for evidence in item.gold_evidence_spans:
            assert evidence.span in by_id[evidence.doc_id].text
    assert len(QUESTIONS) == 16
