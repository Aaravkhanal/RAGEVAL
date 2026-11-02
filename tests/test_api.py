"""Unit tests for FastAPI endpoints."""

import json

import pytest
from fastapi.testclient import TestClient

from rageval import __version__
from rageval.server.app import app
from rageval.server.runtime import cors_allow_origins, reset_runtime_for_tests

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_runtime():
    reset_runtime_for_tests()
    yield
    reset_runtime_for_tests()


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["service"] == "rageval"
    assert body["version"] == __version__
    assert "busy" in body
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("x-request-id")


def test_health_echoes_request_id():
    res = client.get("/health", headers={"X-Request-ID": "req-test-1"})
    assert res.headers.get("x-request-id") == "req-test-1"


def test_public_mode_protects_data_results_and_evaluation(monkeypatch):
    monkeypatch.setenv("RAGEVAL_REQUIRE_AUTH", "1")
    monkeypatch.setenv("RAGEVAL_PUBLIC_TOKEN", "test-public-token")
    for method, path in [
        ("get", "/datasets/benchmark_v1"),
        ("get", "/experiments/example/results"),
        ("get", "/metrics/summary"),
        ("post", "/evaluate/answer"),
        ("post", "/score"),
    ]:
        assert getattr(client, method)(path).status_code == 401
    assert client.get("/health").status_code == 200
    headers = {"X-RAGEVAL-API-TOKEN": "test-public-token"}
    assert client.get("/datasets/benchmark_v1", headers=headers).status_code == 200
    assert client.get("/experiments/example/results", headers=headers).status_code == 404


def test_public_mode_fails_closed_without_token(monkeypatch):
    monkeypatch.setenv("RAGEVAL_REQUIRE_AUTH", "1")
    monkeypatch.delenv("RAGEVAL_PUBLIC_TOKEN", raising=False)
    assert client.get("/datasets").status_code == 503


def test_nonlocal_serve_requires_public_auth(monkeypatch):
    import os
    import subprocess
    import sys

    monkeypatch.delenv("RAGEVAL_REQUIRE_AUTH", raising=False)
    monkeypatch.delenv("RAGEVAL_PUBLIC_TOKEN", raising=False)
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"RAGEVAL_REQUIRE_AUTH", "RAGEVAL_PUBLIC_TOKEN", "RAGEVAL_ADMIN_TOKEN"}
    }
    env["RAGEVAL_REQUIRE_AUTH"] = "0"
    env["RAGEVAL_PUBLIC_TOKEN"] = "unset-for-test"
    result = subprocess.run(
        [sys.executable, "-m", "rageval.cli", "serve", "--host", "0.0.0.0"],
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    assert result.returncode != 0
    assert "requires RAGEVAL_REQUIRE_AUTH=1" in result.stderr


def test_public_read_rate_limit(monkeypatch):
    monkeypatch.setenv("RAGEVAL_REQUIRE_AUTH", "1")
    monkeypatch.setenv("RAGEVAL_PUBLIC_TOKEN", "test-public-token")
    monkeypatch.setenv("RAGEVAL_READ_RATE_LIMIT_PER_MINUTE", "2")
    headers = {"X-RAGEVAL-API-TOKEN": "test-public-token"}
    assert client.get("/datasets", headers=headers).status_code == 200
    assert client.get("/datasets", headers=headers).status_code == 200
    limited = client.get("/datasets", headers=headers)
    assert limited.status_code == 429
    assert limited.headers["retry-after"] == "60"


def test_ready_check():
    res = client.get("/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ready"
    assert body["data_ok"] is True
    assert body["version"] == __version__


def test_ready_requires_runs_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("RAGEVAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("RAGEVAL_RUNS_DIR", str(tmp_path / "missing"))
    res = client.get("/ready")
    assert res.status_code == 503
    assert res.json()["runs_ok"] is False


def test_experiment_start_requires_admin_token(monkeypatch):
    monkeypatch.delenv("RAGEVAL_ADMIN_TOKEN", raising=False)
    res = client.post("/experiments", json={"config": "smoke"})
    assert res.status_code == 503
    monkeypatch.setenv("RAGEVAL_ADMIN_TOKEN", "test-admin-token")
    res = client.post("/experiments", json={"config": "smoke"})
    assert res.status_code == 401
    res = client.post("/experiments", json={"config": "smoke"}, headers={"X-RAGEVAL-ADMIN-TOKEN": "wrong"})
    assert res.status_code == 401


def test_large_evaluation_request_rejected():
    res = client.post("/evaluate/answer", json={"question": "q", "answer": "x" * 70000})
    assert res.status_code == 413


def test_dashboard_escapes_untrusted_claim_and_context():
    html = client.get("/").text
    assert "escapeHtml(v.claim_text)" in html
    assert "escapeHtml(v.explanation || '')" in html
    assert "marked.textContent = verif.evidence_exact_text" in html
    assert "span.textContent = contextText" in html


def test_evaluate_answer_heuristic_default():
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
    assert data["faithfulness_score"] == 1.0
    assert len(data["claims"]) >= 1
    assert data["verifications"][0]["verifier_method"] == "heuristic"


def test_evaluate_answer_rejects_unknown_method():
    res = client.post(
        "/evaluate/answer",
        json={
            "question": "q",
            "answer": "a",
            "context_chunks": ["c"],
            "method": "magic",
        },
    )
    assert res.status_code == 422


def test_http_nli_is_opt_in(monkeypatch):
    monkeypatch.delenv("RAGEVAL_ENABLE_HTTP_NLI", raising=False)
    res = client.post("/evaluate/answer", json={"question": "q", "answer": "a", "method": "nli"})
    assert res.status_code == 403


def test_score_endpoint_heuristic():
    res = client.post(
        "/score",
        json={
            "question": "What was the margin?",
            "answer": "Gross margin was 78.2% [1].",
            "contexts": ["ApexCloud reported that gross margin reached 78.2% in Q3 2024."],
            "query_id": "http_score_1",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["schema"] == "rageval.external_score.v1"
    assert body["evaluation"]["faithfulness_score"] == 1.0
    assert body["evaluation"]["query_id"] == "http_score_1"


def test_evaluate_rate_limit(monkeypatch):
    monkeypatch.setenv("RAGEVAL_RATE_LIMIT_PER_MINUTE", "2")
    payload = {
        "question": "What is the test question?",
        "answer": "The test is valid [1].",
        "context_chunks": ["The test is valid."],
    }
    codes = [client.post("/evaluate/answer", json=payload).status_code for _ in range(3)]
    assert codes[:2] == [200, 200]
    assert codes[2] == 429


def test_cors_origins_helper():
    origins, creds = cors_allow_origins("http://127.0.0.1:8000,http://localhost:8000")
    assert origins == ["http://127.0.0.1:8000", "http://localhost:8000"]
    assert creds is True
    wild, wild_creds = cors_allow_origins("*")
    assert wild == ["*"]
    assert wild_creds is False


@pytest.mark.hf
def test_evaluate_answer_api(monkeypatch):
    monkeypatch.setenv("RAGEVAL_ENABLE_HTTP_NLI", "1")
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    payload = {
        "question": "What was ApexCloud gross margin?",
        "answer": "ApexCloud reached a 78.2% gross margin [1].",
        "context_chunks": [
            "ApexCloud reported that gross margin reached 78.2% in Q3 2024.",
        ],
        "method": "nli",
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
    assert "/experiment-configs" in paths
    assert "post" in paths["/experiments"]
    assert "/ready" in paths
    assert "/score" in paths
    assert "post" in paths["/score"]


def test_datasets_index_and_detail():
    index = client.get("/datasets")
    assert index.status_code == 200
    ids = {row["dataset_id"] for row in index.json()["datasets"]}
    assert "smoke_v1" in ids
    assert "benchmark_v1" in ids
    detail = client.get("/datasets/benchmark_v1")
    assert detail.status_code == 200
    body = detail.json()
    assert body["n_items"] == 47
    assert body["version"] == "1.4.0"
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


def test_post_experiments_requires_config_name():
    res = client.post("/experiments")
    assert res.status_code == 422


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
    assert "20261029T165024Z_657c8089" in ids
    v11 = client.get("/experiments/20261029T165024Z_657c8089/results")
    assert v11.status_code == 200
    assert v11.json()["metrics"]["n_items"] == 28
    assert "20261029T173408Z_de870a29" in ids
    v12 = client.get("/experiments/20261029T173408Z_de870a29/results")
    assert v12.status_code == 200
    assert v12.json()["metrics"]["n_items"] == 32
    assert "20261029T173515Z_7e2b94a3" in ids
    achunk = client.get("/experiments/20261029T173515Z_7e2b94a3/results")
    assert achunk.status_code == 200
    assert achunk.json()["metrics"]["experiment_id"] == "A_chunk"


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
    assert 'apiFetch("/experiments"' in html
    assert 'apiFetch("/experiment-configs")' in html
    assert 'method: "POST"' in html
    assert "allow_heavy" in html
    assert "Allow heavy (NLI / full v1)" in html
    assert "btn-start-experiment" in html
    assert "api_key" not in html
    assert "OPENAI_API_KEY" not in html
    assert "2000" in html
    assert "eval-method" in html
    assert 'value="heuristic"' in html
    assert "fonts.googleapis.com" not in html
    assert "fonts.gstatic.com" not in html
