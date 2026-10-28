"""Smoke dataset still loads after label taxonomy change."""

from rageval.dataset.loader import DatasetLoader
from rageval.dataset.validator import validate_benchmark_integrity
from rageval.core.labels import VerificationLabel


def test_smoke_dataset_loads_and_maps_labels():
    loader = DatasetLoader("data")
    docs = loader.load_corpus()
    items = loader.load_benchmark("all")
    report = validate_benchmark_integrity(docs, items)
    assert report["valid"] is True
    assert len(docs) == 8
    assert len(items) == 8
    gold_statuses = [c.status for it in items for c in it.gold_atomic_claims]
    assert gold_statuses
    assert all(s == VerificationLabel.SUPPORTED for s in gold_statuses)
