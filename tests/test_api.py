"""Unit tests for FastAPI endpoints."""

import json

from fastapi.testclient import TestClient

from rageval.server.app import app

client = TestClient(app)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "rageval"}


def test_evaluate_answer_api():
    payload = {
        "question": "What was ApexCloud gross margin?",
        "answer": "ApexCloud reached a 78.2% gross margin [1].",
        "context_chunks": [
            "ApexCloud reported that gross margin reached 78.2% in Q3 2024.",
        ],
    }
    res = client.post("/evaluate/answer", json=payload)
    assert res.status_code == 200
    data = res.json()["evaluation"]
    assert "faithfulness_score" in data
    assert data["faithfulness_score"] == 1.0
    assert len(data["claims"]) >= 1
    assert data["verifications"][0]["label"] == "supported"


def test_openapi_lists_catalog_routes():
    spec = client.get("/openapi.json").json()
    paths = spec["paths"]
    assert "/datasets" in paths
    assert "/datasets/{dataset_id}" in paths
    assert "/experiments" in paths
    assert "/experiments/{run_id}" in paths
    assert "/experiments/{run_id}/results" in paths


def test_datasets_index_and_detail():
    index = client.get("/datasets")
    assert index.status_code == 200
    ids = {row["dataset_id"] for row in index.json()["datasets"]}
    assert "smoke_v1" in ids
    assert "benchmark_v1" in ids
    detail = client.get("/datasets/benchmark_v1")
    assert detail.status_code == 200
    body = detail.json()
    assert body["n_items"] == 28
    assert any("Apollo" in item["question"] or "influenza" in item["question"].lower() for item in body["items"])
    assert "api_key" not in json.dumps(body)


def test_unknown_dataset_404():
    res = client.get("/datasets/not_a_dataset")
    assert res.status_code == 404


def test_invalid_dataset_id_400():
    res = client.get("/datasets/bad..id")
    assert res.status_code == 400


def test_benchmark_run_gone():
    res = client.post("/benchmark/run")
    assert res.status_code == 410
    assert "CLI" in res.json()["detail"] or "rageval experiment" in res.json()["detail"]


def test_post_experiments_not_implemented():
    res = client.post("/experiments")
    assert res.status_code == 501
    assert "rageval experiment" in res.json()["detail"]


def test_experiments_committed_snapshot_results():
    listing = client.get("/experiments")
    assert listing.status_code == 200
    ids = {row["id"] for row in listing.json()["experiments"]}
    assert "20261028T183042Z_a97ad68f" in ids
    res = client.get("/experiments/20261028T183042Z_a97ad68f/results")
    assert res.status_code == 200
    body = res.json()
    assert body["metrics"]["n_items"] == 24
    assert body["table"]
    assert "run_dir" not in json.dumps(body)


def test_experiment_secret_redaction(tmp_path, monkeypatch):
    monkeypatch.setenv("RAGEVAL_RUNS_DIR", str(tmp_path))
    monkeypatch.setenv("RAGEVAL_INCLUDE_SNAPSHOTS", "0")
    run = tmp_path / "secret_run"
    run.mkdir()
    (run / "manifest.json").write_text(
        json.dumps(
            {
                "run_dir": str(run.resolve()),
                "openai_api_key": "sk-should-not-leak",
                "dataset_id": "smoke_v1",
            }
        ),
        encoding="utf-8",
    )
    (run / "metrics.json").write_text(
        json.dumps({"by_config": {}, "n_items": 0, "label": "secret"}),
        encoding="utf-8",
    )
    res = client.get("/experiments/secret_run")
    assert res.status_code == 200
    dumped = json.dumps(res.json())
    assert "sk-should-not-leak" not in dumped
    assert "<redacted>" in dumped
    assert str(run.resolve()) not in dumped


def test_path_traversal_experiment_rejected():
    res = client.get("/experiments/bad..id")
    assert res.status_code == 400


def test_dashboard_html_is_api_backed():
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert "Form 10-Q SEC Filing" not in html
    assert "Execute Full Ablation Run" not in html
    assert "/benchmark/run" not in html
    assert "GET /datasets" in html
    assert "/experiments/" in html
