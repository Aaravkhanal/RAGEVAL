"""R3: opt-in LLM smoke is CLI-gated; HTTP never lists or runs it."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rageval.benchmark.experiments import load_experiment, run_experiment
from rageval.core.config import (
    ChunkerConfig,
    EvaluatorConfig,
    ExperimentSpec,
    GeneratorConfig,
    PipelineConfig,
    RerankerConfig,
    RetrieverConfig,
)
from rageval.server.app import app
from rageval.server.jobs import resolve_config_path
from rageval.server.runtime import reset_runtime_for_tests

client = TestClient(app)


@pytest.fixture(autouse=True)
def _job_auth(monkeypatch):
    reset_runtime_for_tests()
    monkeypatch.setenv("RAGEVAL_ADMIN_TOKEN", "test-admin-token")
    client.headers.update({"X-RAGEVAL-ADMIN-TOKEN": "test-admin-token"})
    yield
    client.headers.pop("X-RAGEVAL-ADMIN-TOKEN", None)
    reset_runtime_for_tests()


def test_nvidia_nim_yaml_is_opt_in_without_secrets():
    spec = load_experiment("configs/opt_in/smoke_llm_nvidia.yaml")
    assert spec.experiment_id == "smoke_llm_nvidia"
    assert spec.opt_in is True
    assert spec.dataset_id == "smoke_v1"
    assert spec.pipelines
    gen = spec.pipelines[0].generator
    assert gen.backend == "openai"
    assert gen.api_key_env == "NVIDIA_API_KEY"
    assert gen.base_url == "https://integrate.api.nvidia.com/v1"
    assert gen.model_name == "nvidia/nemotron-3.5-bolt-e4b"
    dumped = spec.model_dump_json()
    assert "nvapi-" not in dumped
    yaml_text = Path("configs/opt_in/nvidia_nim.yaml").read_text(encoding="utf-8")
    assert "nvapi-" not in yaml_text
    assert "api_key_env: NVIDIA_API_KEY" in yaml_text


def test_nvidia_benchmark_yaml_is_opt_in_nli_without_secrets():
    spec = load_experiment("configs/opt_in/benchmark_llm_nvidia.yaml")
    assert spec.experiment_id == "nvidia_nim_v1"
    assert spec.opt_in is True
    assert spec.dataset_id == "benchmark_v1"
    assert spec.label == "pilot"
    gen = spec.pipelines[0].generator
    assert gen.backend == "openai"
    assert gen.api_key_env == "NVIDIA_API_KEY"
    assert gen.model_name == "nvidia/nemotron-3.5-bolt-e4b"
    assert spec.pipelines[0].evaluator.method == "nli"
    dumped = spec.model_dump_json()
    assert "nvapi-" not in dumped
    yaml_text = Path("configs/opt_in/nvidia_nim_nli.yaml").read_text(encoding="utf-8")
    assert "nvapi-" not in yaml_text


def test_nvidia_retrieve_yaml_is_two_opt_in_pipelines():
    spec = load_experiment("configs/opt_in/benchmark_llm_nvidia_retrieve.yaml")
    assert spec.experiment_id == "nvidia_nim_retrieve"
    assert spec.opt_in is True
    assert spec.dataset_id == "benchmark_v1"
    assert len(spec.pipelines) == 2
    methods = {p.retriever.method for p in spec.pipelines}
    assert methods == {"dense", "hybrid"}
    assert all(p.generator.api_key_env == "NVIDIA_API_KEY" for p in spec.pipelines)
    assert all(p.evaluator.method == "nli" for p in spec.pipelines)
    assert "nvapi-" not in spec.model_dump_json()


def test_smoke_llm_yaml_is_opt_in_experiment():
    spec = load_experiment("configs/opt_in/smoke_llm.yaml")
    assert spec.experiment_id == "smoke_llm"
    assert spec.opt_in is True
    assert spec.dataset_id == "smoke_v1"
    assert spec.resource_note
    assert spec.pipelines
    assert spec.pipelines[0].generator.backend == "openai"
    dumped = spec.model_dump_json()
    assert "api_key" not in dumped or '"api_key"' not in dumped
    assert "sk-" not in dumped


def test_opt_in_experiment_refuses_without_flag(tmp_path):
    spec = load_experiment("configs/opt_in/smoke_llm.yaml")
    with pytest.raises(RuntimeError, match="--allow-opt-in"):
        run_experiment(spec, output_root=str(tmp_path), max_items=1)


def test_opt_in_without_resource_note_refuses_even_with_flag(tmp_path):
    spec = ExperimentSpec(
        experiment_id="opt_in_empty_note",
        label="pilot",
        dataset_id="smoke_v1",
        opt_in=True,
        resource_note="",
        pipelines=[
            PipelineConfig(
                name="opt_in_mock",
                opt_in=True,
                chunker=ChunkerConfig(chunk_size=128, chunk_overlap=32),
                retriever=RetrieverConfig(method="sparse", top_k=5),
                reranker=RerankerConfig(enabled=False),
                generator=GeneratorConfig(backend="mock", mock_mode="faithful"),
                evaluator=EvaluatorConfig(method="heuristic"),
            )
        ],
    )
    with pytest.raises(RuntimeError, match="resource_note"):
        run_experiment(spec, output_root=str(tmp_path), max_items=1, allow_opt_in=True)


def test_opt_in_mock_runs_when_allowed(tmp_path):
    spec = ExperimentSpec(
        experiment_id="opt_in_mock_allowed",
        label="pilot",
        dataset_id="smoke_v1",
        opt_in=True,
        resource_note="test-only mock labeled opt_in; not a live LLM.",
        pipelines=[
            PipelineConfig(
                name="opt_in_mock",
                opt_in=True,
                resource_note="test-only mock labeled opt_in; not a live LLM.",
                chunker=ChunkerConfig(chunk_size=128, chunk_overlap=32),
                retriever=RetrieverConfig(method="sparse", top_k=5),
                reranker=RerankerConfig(enabled=False),
                generator=GeneratorConfig(backend="mock", mock_mode="faithful"),
                evaluator=EvaluatorConfig(method="heuristic"),
            )
        ],
    )
    run_dir = run_experiment(
        spec,
        data_dir="data",
        output_root=str(tmp_path),
        max_items=1,
        allow_opt_in=True,
    )
    assert (Path(run_dir) / "metrics.json").is_file()


def test_http_does_not_resolve_smoke_llm():
    with pytest.raises(FileNotFoundError):
        resolve_config_path("smoke_llm")
    res = client.post("/experiments", json={"config": "smoke_llm", "max_items": 1})
    assert res.status_code == 400
    assert "Unknown experiment config" in res.json()["detail"]


def test_http_does_not_resolve_smoke_llm_nvidia():
    with pytest.raises(FileNotFoundError):
        resolve_config_path("smoke_llm_nvidia")
    res = client.post("/experiments", json={"config": "smoke_llm_nvidia", "max_items": 1})
    assert res.status_code == 400
    assert "Unknown experiment config" in res.json()["detail"]
    with pytest.raises(FileNotFoundError):
        resolve_config_path("nvidia_nim_v1")
    res = client.post("/experiments", json={"config": "nvidia_nim_v1", "max_items": 1})
    assert res.status_code == 400


def test_http_refuses_opt_in_even_if_copied_into_experiments(tmp_path, monkeypatch):
    from rageval.server import jobs as jobs_mod

    root = tmp_path / "experiments"
    root.mkdir()
    (root / "sneaky.yaml").write_text(
        "experiment_id: sneaky\n"
        "label: pilot\n"
        "dataset_id: smoke_v1\n"
        "opt_in: true\n"
        "resource_note: would call a live LLM\n"
        "pipelines:\n"
        "  - name: sneaky_mock\n"
        "    opt_in: true\n"
        "    generator:\n"
        "      backend: mock\n"
        "    evaluator:\n"
        "      method: heuristic\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(jobs_mod, "EXPERIMENTS_DIR", str(root))
    with pytest.raises(PermissionError, match="opt-in"):
        jobs_mod.enqueue_experiment("sneaky", max_items=1, allow_heavy=True)


def test_cli_opt_in_without_flag_exits(tmp_path):
    import subprocess
    import sys

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "rageval.cli",
            "experiment",
            "--config",
            "configs/opt_in/smoke_llm.yaml",
            "--output-dir",
            str(tmp_path),
            "--max-items",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "--allow-opt-in" in (proc.stderr + proc.stdout)
