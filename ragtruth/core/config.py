"""Configuration loader and schema definitions for RAGTruth experiments."""

from __future__ import annotations
import os
import yaml
from typing import Optional, List
from pydantic import BaseModel, Field


class ChunkerConfig(BaseModel):
    strategy: str = "fixed"  # fixed, recursive, sentence_window
    chunk_size: int = 256
    chunk_overlap: int = 32
    window_size: int = 3  # for sentence_window


class EmbedderConfig(BaseModel):
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: str = "cpu"  # cpu, cuda, mps
    batch_size: int = 32
    normalize_embeddings: bool = True


class RetrieverConfig(BaseModel):
    method: str = "hybrid"  # dense, sparse, hybrid
    top_k: int = 5
    rrf_k: int = 60
    index_type: str = "FlatIP"  # FlatIP, HNSW


class RerankerConfig(BaseModel):
    enabled: bool = False
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_k: int = 3


class GeneratorConfig(BaseModel):
    backend: str = "mock"  # mock, local_hf, openai, ollama
    model_name: str = "meta-llama/Llama-3.2-3B-Instruct"
    temperature: float = 0.0
    max_tokens: int = 512


class EvaluatorConfig(BaseModel):
    nli_model_name: str = "cross-encoder/nli-deberta-v3-base"
    device: str = "cpu"
    batch_size: int = 16
    confidence_threshold: float = 0.5


class PipelineConfig(BaseModel):
    name: str = "baseline_hybrid"
    chunker: ChunkerConfig = Field(default_factory=ChunkerConfig)
    embedder: EmbedderConfig = Field(default_factory=EmbedderConfig)
    retriever: RetrieverConfig = Field(default_factory=RetrieverConfig)
    reranker: RerankerConfig = Field(default_factory=RerankerConfig)
    generator: GeneratorConfig = Field(default_factory=GeneratorConfig)
    evaluator: EvaluatorConfig = Field(default_factory=EvaluatorConfig)


class BenchmarkSuiteConfig(BaseModel):
    name: str = "ragtruth_comprehensive_benchmark"
    data_dir: str = "data"
    output_dir: str = "reports"
    pipelines: List[PipelineConfig] = Field(default_factory=list)


def load_yaml_config(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
