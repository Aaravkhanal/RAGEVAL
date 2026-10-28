"""Ablation benchmark suite executing grid matrix comparisons."""

from __future__ import annotations
from typing import Dict, List, Optional
from rageval.core.schemas import Document, BenchmarkItem, BenchmarkRunSummary
from rageval.core.config import (
    PipelineConfig,
    ChunkerConfig,
    EmbedderConfig,
    RetrieverConfig,
    RerankerConfig,
    GeneratorConfig,
    EvaluatorConfig,
)
from rageval.pipeline.rag import RAGPipeline
from rageval.evaluator.evaluator import RAGEvalEvaluator
from rageval.benchmark.runner import BenchmarkRunner


def get_default_ablation_matrix() -> List[PipelineConfig]:
    """Builds standard research ablation configurations:

    1. Dense (MiniLM) + 128 chunk size
    2. Dense (MiniLM) + 256 chunk size (Baseline)
    3. Dense (MiniLM) + 512 chunk size
    4. Sparse BM25 + 256 chunk size
    5. Hybrid RRF (Dense + BM25) + 256 chunk size
    6. Hybrid RRF + Cross-Encoder Reranker + 256 chunk size
    """
    matrix = [
        # 1. Chunk size 128
        PipelineConfig(
            name="Dense_Chunk128",
            chunker=ChunkerConfig(chunk_size=128, chunk_overlap=16),
            retriever=RetrieverConfig(method="dense", top_k=5),
            reranker=RerankerConfig(enabled=False),
        ),
        # 2. Chunk size 256 (Baseline)
        PipelineConfig(
            name="Dense_Chunk256_Baseline",
            chunker=ChunkerConfig(chunk_size=256, chunk_overlap=32),
            retriever=RetrieverConfig(method="dense", top_k=5),
            reranker=RerankerConfig(enabled=False),
        ),
        # 3. Chunk size 512
        PipelineConfig(
            name="Dense_Chunk512",
            chunker=ChunkerConfig(chunk_size=512, chunk_overlap=64),
            retriever=RetrieverConfig(method="dense", top_k=5),
            reranker=RerankerConfig(enabled=False),
        ),
        # 4. Sparse BM25
        PipelineConfig(
            name="Sparse_BM25_Chunk256",
            chunker=ChunkerConfig(chunk_size=256, chunk_overlap=32),
            retriever=RetrieverConfig(method="sparse", top_k=5),
            reranker=RerankerConfig(enabled=False),
        ),
        # 5. Hybrid RRF
        PipelineConfig(
            name="Hybrid_RRF_Chunk256",
            chunker=ChunkerConfig(chunk_size=256, chunk_overlap=32),
            retriever=RetrieverConfig(method="hybrid", top_k=5),
            reranker=RerankerConfig(enabled=False),
        ),
        # 6. Hybrid RRF + CrossEncoder Reranker
        PipelineConfig(
            name="Hybrid_RRF_Reranked",
            chunker=ChunkerConfig(chunk_size=256, chunk_overlap=32),
            retriever=RetrieverConfig(method="hybrid", top_k=5),
            reranker=RerankerConfig(enabled=True, top_k=3),
        ),
    ]
    return matrix


class BenchmarkSuite:
    """Orchestrates running multiple ablation configurations over a corpus."""

    def __init__(self, configs: Optional[List[PipelineConfig]] = None):
        self.configs = configs or get_default_ablation_matrix()

    def run_suite(
        self,
        documents: List[Document],
        benchmark_items: List[BenchmarkItem],
    ) -> List[BenchmarkRunSummary]:
        summaries: List[BenchmarkRunSummary] = []
        
        # Share a single evaluator instance across runs for memory efficiency
        evaluator = RAGEvalEvaluator(EvaluatorConfig())

        for cfg in self.configs:
            print(f"--> Running ablation configuration: {cfg.name}")
            pipeline = RAGPipeline(cfg)
            runner = BenchmarkRunner(pipeline, evaluator=evaluator)
            summary = runner.run(documents, benchmark_items)
            summaries.append(summary)

        return summaries
