"""Process-local HTTP experiment jobs. POST never runs the suite on the request thread."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rageval.server.app import app
from rageval.server.jobs import (
    LIGHT_CONFIGS,
    list_named_configs,
    reset_job_state_for_tests,
    resolve_config_path,
    run_next_job,
)
from rageval.server.runtime import reset_runtime_for_tests

client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolate_jobs(tmp_path, monkeypatch):
    monkeypatch.setenv("RAGEVAL_RUNS_DIR", str(tmp_path))
    monkeypatch.setenv("RAGEVAL_INCLUDE_SNAPSHOTS", "0")
    monkeypatch.setenv("RAGEVAL_ADMIN_TOKEN", "test-admin-token")
    client.headers.update({"X-RAGEVAL-ADMIN-TOKEN": "test-admin-token"})
    reset_runtime_for_tests()
    reset_job_state_for_tests()
    yield
    reset_job_state_for_tests()
    client.headers.pop("X-RAGEVAL-ADMIN-TOKEN", None)
    reset_runtime_for_tests()


def _poll_until_terminal(run_id: str, timeout: float = 60.0) -> dict:
    run_next_job()
    deadline = time.monotonic() + timeout
    last = {}
    while time.monotonic() < deadline:
        res = client.get(f"/experiments/{run_id}")
        if res.status_code == 404:
            time.sleep(0.05)
            continue
        assert res.status_code == 200, res.text
        last = res.json()
        state = last.get("state") or (last.get("status") or {}).get("state")
        if state in {"complete", "failed"}:
            return last
        time.sleep(0.1)
    raise AssertionError(f"job {run_id} did not finish: {last}")


def test_named_configs_include_smoke_and_heavy():
    names = {row["name"]: row["heavy"] for row in list_named_configs()}
    assert names["smoke"] is False
    assert names["C_retrieve"] is True
    assert names["H_independent"] is True
    assert "smoke" in LIGHT_CONFIGS
    assert "smoke_llm" not in names


def test_resolve_config_rejects_paths():
    with pytest.raises(ValueError, match="invalid"):
        resolve_config_path("../smoke")
    with pytest.raises(ValueError, match="invalid"):
        resolve_config_path("foo/bar")
    with pytest.raises(FileNotFoundError):
        resolve_config_path("not_a_real_config")


def test_experiment_configs_endpoint():
    res = client.get("/experiment-configs")
    assert res.status_code == 200
    body = res.json()
    names = {row["name"] for row in body["configs"]}
    assert "smoke" in names
    assert "C_retrieve" in names
    dumped = json.dumps(body)
    assert "api_key" not in dumped
    assert str(Path.home()) not in dumped


def test_post_max_items_above_cap_422():
    res = client.post("/experiments", json={"config": "smoke", "max_items": 33})
    assert res.status_code == 422


def test_post_unknown_config_400():
    res = client.post("/experiments", json={"config": "not_a_real_config", "max_items": 1})
    assert res.status_code == 400
    assert "Unknown experiment config" in res.json()["detail"]


def test_post_heavy_without_allow_403():
    res = client.post("/experiments", json={"config": "C_retrieve", "max_items": 1})
    assert res.status_code == 403
    assert "allow_heavy" in res.json()["detail"]


def test_light_only_deployment_rejects_heavy_even_when_requested(monkeypatch):
    monkeypatch.setenv("RAGEVAL_LIGHT_ONLY", "1")
    response = client.get("/experiment-configs")
    assert response.status_code == 200
    assert response.json()["light_only"] is True
    names = {row["name"] for row in response.json()["configs"]}
    assert names == {"smoke"}
    res = client.post("/experiments", json={"config": "C_retrieve", "max_items": 1, "allow_heavy": True})
    assert res.status_code == 403
    assert "lightweight" in res.json()["detail"]


def test_post_analysis_only_400():
    res = client.post(
        "/experiments",
        json={"config": "G_claim_vs_answer", "max_items": 1, "allow_heavy": True},
    )
    assert res.status_code == 400
    assert "no pipelines" in res.json()["detail"]


def test_second_post_while_busy_409():
    first = client.post("/experiments", json={"config": "smoke", "max_items": 1})
    assert first.status_code == 202
    res = client.post("/experiments", json={"config": "smoke", "max_items": 1})
    assert res.status_code == 409
    assert "already" in res.json()["detail"].lower()


def test_post_smoke_completes_and_writes_metrics(tmp_path):
    res = client.post("/experiments", json={"config": "smoke", "max_items": 1})
    assert res.status_code == 202
    body = res.json()
    run_id = body["id"]
    assert body["status"] == "queued"
    assert body["poll"] == f"/experiments/{run_id}"
    assert body["config"] == "smoke"
    assert body["max_items"] == 1
    dumped = json.dumps(body)
    assert "api_key" not in dumped
    assert "sk-" not in dumped

    final = _poll_until_terminal(run_id)
    assert final["state"] == "complete"
    assert final.get("has_metrics") is True
    dumped_final = json.dumps(final)
    assert "api_key" not in dumped_final
    assert str(Path.home()) not in dumped_final or "<redacted>" in dumped_final

    results = client.get(f"/experiments/{run_id}/results")
    assert results.status_code == 200
    metrics = results.json()["metrics"]
    assert metrics["n_items"] == 1
    assert metrics.get("experiment_id") == "smoke"
    assert (tmp_path / run_id / "metrics.json").is_file()
    assert (tmp_path / run_id / "status.json").is_file()


def test_expired_running_job_is_recovered(tmp_path):
    res = client.post("/experiments", json={"config": "smoke", "max_items": 1})
    assert res.status_code == 202
    run_id = res.json()["id"]
    with sqlite3.connect(tmp_path / "jobs.sqlite3") as conn:
        conn.execute("UPDATE jobs SET state='running',lease_until=0 WHERE id=?", (run_id,))
    assert run_next_job() is True
    assert client.get(f"/experiments/{run_id}").json()["state"] == "complete"
