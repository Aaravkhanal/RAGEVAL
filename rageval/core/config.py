"""Configuration loader and schema definitions for RAGeval experiments."""

from __future__ import annotations

import os
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class ChunkerConfig(BaseModel):
    strategy: str = "fixed"  # fixed, sentence_window, semantic
    chunk_size: int = 256
    chunk_overlap: int = 32
    window_size: int = 3


class EmbedderConfig(BaseModel):
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: str = "cpu"
    batch_size: int = 32
    normalize_embeddings: bool = True


class RetrieverConfig(BaseModel):
    method: str = "hybrid"  # dense, sparse, hybrid
    top_k: int = 5
    rrf_k: int = 60
    index_type: str = "FlatIP"


class RerankerConfig(BaseModel):
    enabled: bool = False
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_k: int = 3


class GeneratorConfig(BaseModel):
    backend: str = "mock"  # mock, openai, ollama
    model_name: str = "meta-llama/Llama-3.2-3B-Instruct"
    temperature: float = 0.0
    max_tokens: int = 512
    mock_mode: str = "faithful"  # faithful, hallucinatory, contradictory, mixed
    abstention_policy: str = "empty_context"  # never, empty_context


class EvaluatorConfig(BaseModel):
    method: str = "nli"  # nli, heuristic
    nli_model_name: str = "cross-encoder/nli-deberta-v3-base"
    device: str = "cpu"
    batch_size: int = 16
    confidence_threshold: float = 0.5
    allow_heuristic_fallback: bool = False
    enable_multi_hop: bool = False
    prompt_usd_per_million: Optional[float] = None
    completion_usd_per_million: Optional[float] = None
    pricing_source: Optional[str] = None


class PipelineConfig(BaseModel):
    name: str = "baseline_hybrid"
    seed: int = 0
    chunker: ChunkerConfig = Field(default_factory=ChunkerConfig)
    embedder: EmbedderConfig = Field(default_factory=EmbedderConfig)
    retriever: RetrieverConfig = Field(default_factory=RetrieverConfig)
    reranker: RerankerConfig = Field(default_factory=RerankerConfig)
    generator: GeneratorConfig = Field(default_factory=GeneratorConfig)
    evaluator: EvaluatorConfig = Field(default_factory=EvaluatorConfig)


class BenchmarkSuiteConfig(BaseModel):
    name: str = "rageval_comprehensive_benchmark"
    data_dir: str = "data"
    output_dir: str = "experiments/runs"
    dataset_id: str = "smoke_v1"
    dataset_version: str = "1.0.0"
    pipelines: List[PipelineConfig] = Field(default_factory=list)


def load_yaml_config(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def pipeline_config_from_yaml(path: str) -> PipelineConfig:
    data = load_yaml_config(path)
    return PipelineConfig.model_validate(data)
