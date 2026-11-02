"""Configuration loader and schema definitions for RAGeval experiments."""

from __future__ import annotations

import os
from typing import List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field
from rageval.core.assets import resolve_asset


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
    device: str = "cpu"


class GeneratorConfig(BaseModel):
    """Generation backend. API keys are never fields; read them from the environment."""

    model_config = ConfigDict(extra="forbid")

    backend: str = "mock"  # mock, openai, ollama, local_hf
    model_name: str = "meta-llama/Llama-3.2-3B-Instruct"
    temperature: float = 0.0
    max_tokens: int = 512
    timeout_s: float = 60.0
    max_retries: int = 2
    mock_mode: str = "faithful"  # faithful, hallucinatory, contradictory, mixed
    abstention_policy: str = "empty_context"  # never, empty_context
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None  # environment variable *name*, never a secret value
    device: str = "cpu"  # local_hf only


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
    opt_in: bool = False
    resource_note: str = ""
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


ALLOWED_EXPERIMENT_LABELS = frozenset({"v1", "pilot", "companion"})


class ExperimentSpec(BaseModel):
    """Named experiment YAML. `label` is `v1`, `pilot`, or `companion`."""

    experiment_id: str
    label: str = "pilot"
    title: str = ""
    family: str = ""
    dataset_id: str = "benchmark_v1"
    split: str = "all"
    resource_note: str = ""
    opt_in: bool = False
    analysis: Optional[str] = None
    slice: Optional[str] = None
    pipeline_paths: List[str] = Field(default_factory=list)
    pipelines: List[PipelineConfig] = Field(default_factory=list)
    opt_in_embedders: List[dict] = Field(default_factory=list)

    def resolved_pipelines(self) -> List[PipelineConfig]:
        return list(self.pipelines)


def pipeline_identity(configs: List[PipelineConfig]) -> List[dict]:
    """Compact generator/retriever/evaluator identity for metrics.json."""
    rows = []
    for cfg in configs:
        rows.append(
            {
                "name": cfg.name,
                "generator_backend": cfg.generator.backend,
                "generator_model": cfg.generator.model_name,
                "retriever": cfg.retriever.method,
                "evaluator_method": cfg.evaluator.method,
                "opt_in": bool(cfg.opt_in),
            }
        )
    return rows


def load_yaml_config(path: str) -> dict:
    path = resolve_asset(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def pipeline_config_from_yaml(path: str) -> PipelineConfig:
    data = load_yaml_config(path)
    return PipelineConfig.model_validate(data)


def experiment_spec_from_yaml(path: str) -> ExperimentSpec:
    path = resolve_asset(path)
    data = load_yaml_config(path)
    raw_paths = list(data.pop("pipeline_paths", []) or [])
    spec = ExperimentSpec.model_validate(data)
    configs = list(spec.pipelines)
    base_dir = os.path.dirname(os.path.abspath(path))
    cwd = os.getcwd()
    for rel in raw_paths:
        candidates = [
            rel,
            os.path.join(cwd, rel),
            os.path.join(base_dir, rel),
            os.path.normpath(os.path.join(base_dir, rel)),
            resolve_asset(rel),
            resolve_asset(os.path.normpath(os.path.join("configs", "experiments", rel))),
        ]
        resolved = next((c for c in candidates if os.path.isfile(c)), None)
        if resolved is None:
            raise FileNotFoundError(f"Pipeline YAML not found for {rel!r} (experiment {path})")
        configs.append(pipeline_config_from_yaml(resolved))
    spec.pipelines = configs
    spec.pipeline_paths = raw_paths
    if spec.label not in ALLOWED_EXPERIMENT_LABELS:
        allowed = ", ".join(sorted(ALLOWED_EXPERIMENT_LABELS))
        raise ValueError(f"experiment label must be one of {allowed}, got {spec.label!r}")
    return spec
