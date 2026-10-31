"""Dataset schema and split validation."""

import pytest

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
    assert all(doc.license == "original-synthetic-in-repo" for doc in docs)
    assert all(doc.provenance for doc in docs)


def test_unknown_split_is_rejected():
    with pytest.raises(ValueError, match="Unknown benchmark split"):
        DatasetLoader("data", dataset_id="benchmark_v1").load_benchmark("tset")


def test_independent_split_loads_for_benchmark_v1():
    items = DatasetLoader("data", dataset_id="benchmark_v1").load_benchmark("independent")
    assert items
    with pytest.raises(ValueError, match="no independent split"):
        DatasetLoader("data").load_benchmark("independent")
