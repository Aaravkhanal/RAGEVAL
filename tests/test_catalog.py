"""Catalog helpers: sanitize secrets, list datasets, resolve runs."""

import json
from pathlib import Path

from rageval.server.catalog import (
    get_dataset,
    get_experiment_results,
    list_datasets,
    list_experiments,
    sanitize,
    table_from_metrics,
)


def test_sanitize_redacts_secrets_and_run_dir():
    payload = sanitize(
        {
            "run_dir": "/Users/secret/experiments/runs/abc",
            "openai_api_key": "sk-live",
            "nested": {"hf_token": "hf_xxx", "label": "pilot"},
        }
    )
    assert "run_dir" not in payload
    assert payload["openai_api_key"] == "<redacted>"
    assert payload["nested"]["hf_token"] == "<redacted>"
    assert payload["nested"]["label"] == "pilot"


def test_list_datasets_includes_smoke_and_v1():
    ids = {row["dataset_id"] for row in list_datasets("data")}
    assert "smoke_v1" in ids
    assert "benchmark_v1" in ids


def test_get_dataset_items_are_licensed_corpus_not_sec_html():
    ds = get_dataset("benchmark_v1", root="data", include_items=True)
    assert ds["version"] == "1.3.0"
    assert ds["n_items"] == 40
    assert ds["n_documents"] == 29
    assert ds["n_independent"] == 23
    questions = " ".join(item["question"] for item in ds["items"])
    assert "Apollo" in questions or "influenza" in questions.lower() or "Yellowstone" in questions
    assert "Form 10-Q" not in questions


def test_list_experiments_tmp_run(tmp_path, monkeypatch):
    monkeypatch.setenv("RAGEVAL_INCLUDE_SNAPSHOTS", "0")
    monkeypatch.setenv("RAGEVAL_RUNS_DIR", str(tmp_path))
    run = tmp_path / "run_toy"
    run.mkdir()
    (run / "metrics.json").write_text(
        json.dumps(
            {
                "label": "pilot",
                "dataset_id": "smoke_v1",
                "n_items": 2,
                "by_config": {
                    "toy": {
                        "n": 2,
                        "claim_support_rate": {"mean": 0.5},
                        "unsupported_claim_rate": {"mean": 0.5},
                        "contradiction_rate": {"mean": 0.0},
                        "recall_at_5": {"mean": 1.0},
                        "mrr": {"mean": 1.0},
                        "abstention_accuracy": 0.0,
                        "mean_latency_ms": 3.0,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    listed = list_experiments(str(tmp_path))
    assert listed[0]["id"] == "run_toy"
    assert listed[0]["has_metrics"] is True
    results = get_experiment_results("run_toy", root=str(tmp_path))
    assert results["table"][0]["config_name"] == "toy"
    assert results["table"][0]["mean_faithfulness"] == 0.5


def test_table_from_metrics_empty():
    assert table_from_metrics({}) == []


def test_committed_snapshot_listed_when_enabled(monkeypatch):
    monkeypatch.delenv("RAGEVAL_INCLUDE_SNAPSHOTS", raising=False)
    monkeypatch.setenv("RAGEVAL_RUNS_DIR", str(Path("experiments") / "missing_runs"))
    ids = {row["id"] for row in list_experiments()}
    assert "20261028T183042Z_a97ad68f" in ids
    payload = get_experiment_results("20261028T183042Z_a97ad68f")
    assert payload["metrics"]["n_items"] == 24
    assert payload["table"]
    assert "20261029T165024Z_657c8089" in ids
    v11 = get_experiment_results("20261029T165024Z_657c8089")
    assert v11["metrics"]["n_items"] == 28
    assert v11["metrics"]["dataset_version"] == "1.1.0"
    assert "20261029T173408Z_de870a29" in ids
    v12 = get_experiment_results("20261029T173408Z_de870a29")
    assert v12["metrics"]["n_items"] == 32
    assert v12["metrics"]["dataset_version"] == "1.2.0"
    assert "20261029T173515Z_7e2b94a3" in ids
    achunk = get_experiment_results("20261029T173515Z_7e2b94a3")
    assert achunk["metrics"]["n_items"] == 32
    assert achunk["metrics"]["experiment_id"] == "A_chunk"
