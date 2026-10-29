"""Phase 7 experiment YAML, dry-run, and metrics.json tables."""

import json
from pathlib import Path

import pytest

from rageval.analysis.generate_paper_report import write_report_from_metrics
from rageval.benchmark.experiments import (
    dry_run_two_configs,
    list_experiment_paths,
    load_experiment,
    run_experiment,
)
from rageval.benchmark.reporter import BenchmarkReporter
from rageval.core.config import (
    ChunkerConfig,
    EvaluatorConfig,
    GeneratorConfig,
    PipelineConfig,
    RerankerConfig,
    RetrieverConfig,
)
from rageval.dataset.loader import DatasetLoader


def test_experiment_yamls_load():
    paths = list_experiment_paths()
    ids = []
    for path in paths:
        spec = load_experiment(path)
        ids.append(spec.experiment_id)
        assert spec.label in {"v1", "pilot"}
        assert spec.resource_note
    assert ids == [
        "A_chunk",
        "B_embed",
        "C_retrieve",
        "D_rerank",
        "E_verifier",
        "F_ablate",
        "G_claim_vs_answer",
    ]
    a = load_experiment("configs/experiments/A_chunk.yaml")
    assert len(a.pipelines) == 3
    assert all(p.chunker.chunk_overlap == 32 for p in a.pipelines)
    b = load_experiment("configs/experiments/B_embed.yaml")
    assert b.opt_in_embedders and b.opt_in_embedders[0]["approved"] is False
    g = load_experiment("configs/experiments/G_claim_vs_answer.yaml")
    assert g.analysis == "claim_vs_answer"
    assert g.pipelines == []
    e = load_experiment("configs/experiments/E_verifier.yaml")
    methods = {p.evaluator.method for p in e.pipelines}
    assert methods == {"nli", "heuristic"}


def test_g_experiment_refuses_to_run_without_pipelines(tmp_path):
    spec = load_experiment("configs/experiments/G_claim_vs_answer.yaml")
    with pytest.raises(ValueError, match="no pipelines"):
        run_experiment(spec, output_root=str(tmp_path))


def test_dry_run_one_item_two_configs(tmp_path):
    loader = DatasetLoader("data", dataset_id="smoke_v1")
    docs = loader.load_corpus()
    item = loader.load_benchmark("all")[0]
    cfgs = [
        PipelineConfig(
            name="pilot_sparse_a",
            chunker=ChunkerConfig(chunk_size=128, chunk_overlap=32),
            retriever=RetrieverConfig(method="sparse", top_k=5),
            reranker=RerankerConfig(enabled=False),
            generator=GeneratorConfig(backend="mock", mock_mode="faithful"),
            evaluator=EvaluatorConfig(method="heuristic"),
        ),
        PipelineConfig(
            name="pilot_sparse_b",
            chunker=ChunkerConfig(chunk_size=256, chunk_overlap=32),
            retriever=RetrieverConfig(method="sparse", top_k=5),
            reranker=RerankerConfig(enabled=False),
            generator=GeneratorConfig(backend="mock", mock_mode="faithful"),
            evaluator=EvaluatorConfig(method="heuristic"),
        ),
    ]
    run_dir = dry_run_two_configs(
        docs, [item], cfgs, output_root=str(tmp_path), run_id="phase7_dry"
    )
    metrics_path = Path(run_dir) / "metrics.json"
    assert metrics_path.is_file()
    metrics = json.loads(metrics_path.read_text())
    assert metrics["overall_score"] is None
    assert metrics["label"] == "pilot"
    assert set(metrics["by_config"]) == {"pilot_sparse_a", "pilot_sparse_b"}
    status = json.loads((Path(run_dir) / "status.json").read_text())
    assert status["state"] == "complete"

    md = BenchmarkReporter.markdown_from_metrics(metrics)
    assert "**Label:** `pilot`" in md
    assert "overall score" in md.lower() or "No official composite" in md or "no overall score" in md.lower()

    report = write_report_from_metrics(metrics, str(tmp_path / "out"))
    text = Path(report).read_text()
    assert "0.938" not in text
    assert "FINDINGS.md" in text
    assert "metrics.json" in text
