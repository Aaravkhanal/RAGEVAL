"""Core Pydantic models and data contracts for the RAGeval benchmark."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from rageval.core.labels import VerificationLabel, parse_verification_label


class TestType(str, Enum):
    __test__ = False
    STANDARD = "standard"
    UNANSWERABLE = "unanswerable"
    CONFLICTING = "conflicting"
    DISTRACTOR = "distractor"


class Document(BaseModel):
    id: str
    text: str
    title: Optional[str] = None
    domain: Optional[str] = "general"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    id: str
    doc_id: str
    text: str
    chunk_index: int
    token_count: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    chunk: Chunk
    score: float
    rank: int
    retrieval_method: str = "dense"


class GoldEvidence(BaseModel):
    doc_id: str
    span: str
    chunk_id: Optional[str] = None
    passage_id: Optional[str] = None


class GoldClaim(BaseModel):
    claim: str
    status: VerificationLabel
    gold_doc_ids: List[str] = Field(default_factory=list)

    @field_validator("status", mode="before")
    @classmethod
    def _parse_status(cls, value: Any) -> VerificationLabel:
        return parse_verification_label(value)


class BenchmarkItem(BaseModel):
    id: str
    domain: str = "general"
    question: str
    gold_answer: Optional[str] = None
    gold_evidence_spans: List[GoldEvidence] = Field(default_factory=list)
    gold_atomic_claims: List[GoldClaim] = Field(default_factory=list)
    test_type: TestType = TestType.STANDARD
    expected_abstention: bool = False
    answerability: str = "answerable"
    scenario_type: str = "standard"
    split: str = "smoke"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AtomicClaim(BaseModel):
    claim_id: str
    text: str
    raw_sentence: str
    cited_chunk_ids: List[str] = Field(default_factory=list)
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    is_abstention: bool = False


class ClaimVerification(BaseModel):
    claim_id: str
    claim_text: str
    label: VerificationLabel
    confidence: Optional[float] = None
    entailment_prob: float = 0.0
    neutral_prob: float = 0.0
    contradiction_prob: float = 0.0
    supporting_chunk_ids: List[str] = Field(default_factory=list)
    contradicting_chunk_ids: List[str] = Field(default_factory=list)
    best_matching_chunk_id: Optional[str] = None
    best_matching_chunk_text: Optional[str] = None
    evidence_span_start: Optional[int] = None
    evidence_span_end: Optional[int] = None
    evidence_exact_text: Optional[str] = None
    explanation: Optional[str] = None
    verifier_method: str = "nli"

    @field_validator("label", mode="before")
    @classmethod
    def _parse_label(cls, value: Any) -> VerificationLabel:
        return parse_verification_label(value)


class CitationMetric(BaseModel):
    total_citations: int
    valid_citations: int
    hallucinated_citations: List[str] = Field(default_factory=list)
    misattributed_citations: List[str] = Field(default_factory=list)
    citation_precision: float
    citation_recall: float
    citation_support_precision: float = 0.0
    citation_completeness: float = 0.0


class RetrievalMetrics(BaseModel):
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    recall_at_k: float = 0.0
    mrr: float = 0.0
    ndcg_at_k: float = 0.0
    noise_ratio: float = 0.0
    retrieved_count: int = 0


class QueryEvaluationResult(BaseModel):
    query_id: str
    question: str
    test_type: TestType
    generated_answer: str
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list)
    claims: List[AtomicClaim] = Field(default_factory=list)
    verifications: List[ClaimVerification] = Field(default_factory=list)

    faithfulness_score: float
    hallucination_rate: float
    contradiction_rate: float
    claim_coverage: float = 1.0

    citation_metrics: CitationMetric
    retrieval_metrics: RetrievalMetrics

    abstained: bool = False
    correctly_abstained: Optional[bool] = None

    retrieval_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0
    verification_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    token_count_prompt: int = 0
    token_count_completion: int = 0
    estimated_cost_usd: Optional[float] = None
    cost_pricing_source: Optional[str] = None


class BenchmarkRunSummary(BaseModel):
    config_name: str
    total_queries: int
    mean_faithfulness: float
    mean_hallucination_rate: float
    mean_contradiction_rate: float
    mean_citation_precision: float
    mean_citation_recall: float
    mean_recall_at_5: float
    mean_mrr: float
    mean_latency_ms: float
    p95_latency_ms: float
    abstention_accuracy: float
    conflicting_detection_rate: float
    total_estimated_cost_usd: Optional[float] = None
    run_id: Optional[str] = None
    dataset_id: Optional[str] = None
    dataset_version: Optional[str] = None
    git_commit: Optional[str] = None
    results: List[QueryEvaluationResult] = Field(default_factory=list)
