"""Core Pydantic models and data contracts for RAGTruth benchmark and evaluation system."""

from __future__ import annotations
from typing import List, Dict, Optional, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field


class TestType(str, Enum):
    __test__ = False
    STANDARD = "standard"
    UNANSWERABLE = "unanswerable"
    CONFLICTING = "conflicting"
    DISTRACTOR = "distractor"


class VerificationLabel(str, Enum):
    ENTAILEMENT = "ENTAILEMENT"  # Supported by evidence
    CONTRADICTION = "CONTRADICTION"  # Directly refuted by evidence
    NEUTRAL = "NEUTRAL"  # Extrapolated, unsupported, or halllucinated


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
    retrieval_method: str = "dense"  # dense, sparse, hybrid, reranked


class GoldEvidence(BaseModel):
    doc_id: str
    span: str
    chunk_id: Optional[str] = None


class GoldClaim(BaseModel):
    claim: str
    status: VerificationLabel
    gold_doc_ids: List[str] = Field(default_factory=list)


class BenchmarkItem(BaseModel):
    id: str
    domain: str = "general"
    question: str
    gold_answer: Optional[str] = None
    gold_evidence_spans: List[GoldEvidence] = Field(default_factory=list)
    gold_atomic_claims: List[GoldClaim] = Field(default_factory=list)
    test_type: TestType = TestType.STANDARD
    expected_abstention: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AtomicClaim(BaseModel):
    claim_id: str
    text: str
    raw_sentence: str
    cited_chunk_ids: List[str] = Field(default_factory=list)
    char_start: Optional[int] = None
    char_end: Optional[int] = None


class ClaimVerification(BaseModel):
    claim_id: str
    claim_text: str
    label: VerificationLabel
    confidence: float
    entailment_prob: float
    neutral_prob: float
    contradiction_prob: float
    supporting_chunk_ids: List[str] = Field(default_factory=list)
    contradicting_chunk_ids: List[str] = Field(default_factory=list)
    best_matching_chunk_id: Optional[str] = None
    best_matching_chunk_text: Optional[str] = None
    evidence_span_start: Optional[int] = None
    evidence_span_end: Optional[int] = None
    evidence_exact_text: Optional[str] = None
    explanation: Optional[str] = None


class CitationMetric(BaseModel):
    total_citations: int
    valid_citations: int
    hallucinated_citations: List[str] = Field(default_factory=list)
    misattributed_citations: List[str] = Field(default_factory=list)
    citation_precision: float
    citation_recall: float


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
    
    # Faithfulness & Hallucination Scores
    faithfulness_score: float  # Fraction of claims that are ENTAILED
    hallucination_rate: float  # Fraction of claims that are NEUTRAL
    contradiction_rate: float  # Fraction of claims that are CONTRADICTION
    
    # Citation Quality
    citation_metrics: CitationMetric
    
    # Retrieval Quality
    retrieval_metrics: RetrievalMetrics
    
    # Adversarial & Behavior
    abstained: bool = False
    correctly_abstained: Optional[bool] = None
    
    # Efficiency Profiling
    retrieval_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0
    verification_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    token_count_prompt: int = 0
    token_count_completion: int = 0
    estimated_cost_usd: float = 0.0


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
    total_estimated_cost_usd: float
    results: List[QueryEvaluationResult] = Field(default_factory=list)
