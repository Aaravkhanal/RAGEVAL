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
        docs, items, require_license=True, require_verbatim_spans=True, require_reviewed_scenarios=True
    )
    assert report["valid"] is True, report["errors"]
    assert len(docs) == 29
    assert len(items) == 40
    assert all(doc.license for doc in docs)
    n_dev = sum(1 for item in items if item.split == "dev")
    n_test = sum(1 for item in items if item.split == "test")
    assert n_dev == 32
    assert n_test == 8
    ids = [item.id for item in items]
    assert ids[-8:] == [
        "v1_033",
        "v1_034",
        "v1_035",
        "v1_036",
        "v1_037",
        "v1_038",
        "v1_039",
        "v1_040",
    ]
    new_ids = {f"v1_{i:03d}" for i in range(29, 41)}
    assert all(item.split == "dev" for item in items if item.id in new_ids)
    frozen_test = {"v1_002", "v1_006", "v1_008", "v1_012", "v1_016", "v1_018", "v1_020", "v1_024"}
    assert {item.id for item in items if item.split == "test"} == frozen_test


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
    assert report["total_benchmark_items"] == 40


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


def test_independent_slice_has_disjoint_gold_docs():
    from rageval.dataset.benchmark_v1 import select_independent_items

    loader = DatasetLoader("data", dataset_id=DATASET_ID)
    items = loader.load_benchmark("all")
    independent = loader.load_benchmark("independent")
    built = select_independent_items(items)
    assert [item.id for item in independent] == [item.id for item in built]
    assert independent
    assert len(independent) == 23
    seen = set()
    for item in independent:
        docs = {ev.doc_id for ev in item.gold_evidence_spans}
        assert docs, item.id
        assert docs.isdisjoint(seen)
        seen.update(docs)
    hubble = next(item for item in items if item.id == "v1_037")
    corpus = {doc.id: doc.text for doc in loader.load_corpus()}
    assert "Launch APR 24, 1990." in corpus["doc_nasa_hubble"]
    assert hubble.gold_evidence_spans[0].span in corpus["doc_nasa_hubble"]
