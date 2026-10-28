"""Smoke pipeline: sparse BM25 + blinded mock, no MiniLM/DeBERTa load."""

from rageval.benchmark.run_store import create_run_dir, save_run
from rageval.benchmark.runner import BenchmarkRunner
from rageval.core.config import (
    EvaluatorConfig,
    GeneratorConfig,
    PipelineConfig,
    RerankerConfig,
    RetrieverConfig,
    pipeline_config_from_yaml,
)
from rageval.core.schemas import TestType
from rageval.dataset.loader import DatasetLoader
from rageval.evaluator.evaluator import RAGEvalEvaluator
from rageval.pipeline.rag import RAGPipeline


def test_yaml_ablation_configs_parse():
    names = []
    for path in [
        "configs/ablation/dense_chunk128.yaml",
        "configs/ablation/dense_chunk256.yaml",
        "configs/ablation/dense_chunk512.yaml",
        "configs/ablation/sparse_bm25_256.yaml",
        "configs/ablation/hybrid_rrf_256.yaml",
        "configs/ablation/hybrid_rrf_reranked.yaml",
    ]:
        cfg = pipeline_config_from_yaml(path)
        names.append(cfg.name)
        assert cfg.generator.backend == "mock"
        assert cfg.evaluator.allow_heuristic_fallback is False
    assert names[5] == "Hybrid_RRF_Reranked"
    assert pipeline_config_from_yaml("configs/ablation/hybrid_rrf_reranked.yaml").reranker.enabled is True


def test_sparse_smoke_pipeline_does_not_leak_unanswerable_labels(tmp_path):
    loader = DatasetLoader("data", dataset_id="smoke_v1")
    docs = loader.load_corpus()
    items = loader.load_benchmark("all")
    cfg = PipelineConfig(
        name="smoke_sparse_heuristic",
        retriever=RetrieverConfig(method="sparse", top_k=5),
        reranker=RerankerConfig(enabled=False),
        generator=GeneratorConfig(backend="mock", mock_mode="faithful", abstention_policy="empty_context"),
        evaluator=EvaluatorConfig(method="heuristic"),
    )
    pipeline = RAGPipeline(cfg)
    assert pipeline.embedder is None
    pipeline.index(docs)
    assert pipeline.faiss_index is None
    assert pipeline.bm25_retriever is not None

    unans = next(item for item in items if item.test_type == TestType.UNANSWERABLE)
    answer, retrieved, *_ = pipeline.query(unans.question, item=unans)
    if retrieved:
        assert "do not have sufficient information" not in answer.lower()

    evaluator = RAGEvalEvaluator(cfg.evaluator)
    runner = BenchmarkRunner(pipeline, evaluator=evaluator)
    summary = runner.run(docs, items[:2], dataset_id="smoke_v1", dataset_version="1.0.0")
    assert summary.total_queries == 2
    assert summary.mean_answer_f1 is not None

    run_dir = create_run_dir(str(tmp_path), run_id="smoke_pipe")
    save_run(run_dir, [summary], pipeline_configs=[cfg])
    assert (tmp_path / "smoke_pipe" / "configs" / "smoke_sparse_heuristic.yaml").exists()
    assert (tmp_path / "smoke_pipe" / "predictions.jsonl").exists()
