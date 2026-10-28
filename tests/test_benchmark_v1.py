"""Licensed benchmark_v1 loads, validates, and supports RQ3 mixed-support items."""

from rageval.core.labels import VerificationLabel
from rageval.dataset.benchmark_v1 import DATASET_ID, build_benchmark
from rageval.dataset.loader import DatasetLoader
from rageval.dataset.validator import validate_benchmark_integrity
from rageval.metrics.answer import mixed_support_answer_gap, token_f1


def test_benchmark_v1_integrity_and_licenses():
    loader = DatasetLoader("data", dataset_id=DATASET_ID)
    docs = loader.load_corpus()
    items = loader.load_benchmark("all")
    report = validate_benchmark_integrity(
        docs, items, require_license=True, require_verbatim_spans=True
    )
    assert report["valid"] is True, report["errors"]
    assert len(docs) == 16
    assert len(items) == 24
    assert all(doc.license for doc in docs)
    n_dev = sum(1 for item in items if item.split == "dev")
    n_test = sum(1 for item in items if item.split == "test")
    assert n_dev == 16
    assert n_test == 8


def test_benchmark_v1_builder_matches_files():
    built_docs, built_items = build_benchmark()
    loader = DatasetLoader("data", dataset_id=DATASET_ID)
    file_docs = loader.load_corpus()
    file_items = loader.load_benchmark("all")
    assert [d.id for d in built_docs] == [d.id for d in file_docs]
    assert [i.id for i in built_items] == [i.id for i in file_items]


def test_validate_cli_benchmark_v1():
    import json
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "rageval.cli", "validate", "--dataset", "benchmark_v1"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["valid"] is True
    assert report["total_benchmark_items"] == 24


def test_smoke_loader_still_defaults():
    loader = DatasetLoader("data")
    docs = loader.load_corpus()
    items = loader.load_benchmark("all")
    assert len(docs) == 8
    assert len(items) == 8


def test_mixed_support_items_have_rq3_gap_on_example_answers():
    loader = DatasetLoader("data", dataset_id=DATASET_ID)
    items = loader.load_benchmark("all")
    mixed = [item for item in items if item.scenario_type == "mixed_support"]
    assert len(mixed) == 4
    for item in mixed:
        example = item.metadata["example_mixed_answer"]
        f1 = token_f1(example, item.gold_answer or "")
        labels = [c.status for c in item.gold_atomic_claims]
        assert mixed_support_answer_gap(f1, labels) is True
        assert VerificationLabel.SUPPORTED in labels
        assert any(s != VerificationLabel.SUPPORTED for s in labels)
