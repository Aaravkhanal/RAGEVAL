"""Claim-level faithfulness and attribution evaluator."""

from __future__ import annotations

import time
from typing import List, Optional

from rageval.core.config import EvaluatorConfig
from rageval.core.labels import VerificationLabel
from rageval.core.schemas import (
    BenchmarkItem,
    QueryEvaluationResult,
    RetrievedChunk,
    TestType,
)
from rageval.evaluator.citation_parser import CitationParser
from rageval.evaluator.decomposer import AtomicClaimDecomposer
from rageval.evaluator.nli_verifier import NLIVerifier
from rageval.evaluator.retrieval_metrics import RetrievalMetricsCalculator
from rageval.metrics.claims import claim_coverage, claim_support_rate, contradiction_rate, unsupported_claim_rate


ABSTENTION_MARKERS = (
    "do not have sufficient information",
    "cannot be answered",
    "insufficient context",
    "not enough information",
)


class RAGEvalEvaluator:
    """Decomposes answers, verifies claims against supplied evidence, and scores metrics."""

    def __init__(self, config: Optional[EvaluatorConfig] = None):
        self.config = config or EvaluatorConfig()
        self.nli_verifier = NLIVerifier(self.config)
        self._multi_hop = None
        if self.config.enable_multi_hop:
            from rageval.evaluator.multi_hop import MultiHopEvidenceFusion

            self._multi_hop = MultiHopEvidenceFusion(nli_verifier=self.nli_verifier)

    def evaluate_query(
        self,
        question: str,
        generated_answer: str,
        retrieved_chunks: List[RetrievedChunk],
        item: Optional[BenchmarkItem] = None,
        retrieval_latency_ms: float = 0.0,
        generation_latency_ms: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> QueryEvaluationResult:
        t0 = time.perf_counter()

        claims = AtomicClaimDecomposer.decompose(generated_answer, retrieved_chunks)

        verifications = []
        for claim in claims:
            verif = self.nli_verifier.verify_claim(claim, retrieved_chunks)
            if self._multi_hop and not claim.is_abstention:
                verif = self._multi_hop.evaluate_multi_hop_claim(claim, retrieved_chunks, verif)
            verifications.append(verif)

        citation_metrics = CitationParser.audit_citations_with_claims(
            generated_answer, retrieved_chunks, claims, verifications
        )

        lower_ans = generated_answer.lower()
        abstained = any(term in lower_ans for term in ABSTENTION_MARKERS) or any(c.is_abstention for c in claims)

        assessable_labels = [
            v.label
            for claim, v in zip(claims, verifications)
            if not claim.is_abstention
        ]
        if assessable_labels:
            faithfulness = claim_support_rate(assessable_labels)
            hallucination_rate = unsupported_claim_rate(assessable_labels, include_partial=True)
            contra_rate = contradiction_rate(assessable_labels)
        else:
            # No factual claims: undefined rates default to 1.0 faithfulness iff abstention or empty answer.
            faithfulness = 1.0 if (abstained or not generated_answer.strip()) else 0.0
            hallucination_rate = 0.0
            contra_rate = 0.0
        coverage = claim_coverage(len(claims), len(verifications))

        correctly_abstained: Optional[bool] = None
        if item:
            if item.expected_abstention:
                correctly_abstained = abstained
            else:
                correctly_abstained = not abstained

        if item:
            retrieval_metrics = RetrievalMetricsCalculator.calculate(retrieved_chunks, item)
            query_id = item.id
            test_type = item.test_type
        else:
            retrieval_metrics = RetrievalMetricsCalculator.calculate(
                retrieved_chunks,
                BenchmarkItem(id="live_query", question=question),
            )
            query_id = "live_query"
            test_type = TestType.STANDARD

        verif_latency_ms = (time.perf_counter() - t0) * 1000.0
        total_latency_ms = retrieval_latency_ms + generation_latency_ms + verif_latency_ms

        cost_usd = None
        pricing_source = None
        if (
            self.config.prompt_usd_per_million is not None
            and self.config.completion_usd_per_million is not None
        ):
            cost_usd = (
                (prompt_tokens * self.config.prompt_usd_per_million)
                + (completion_tokens * self.config.completion_usd_per_million)
            ) / 1_000_000.0
            pricing_source = self.config.pricing_source or "EvaluatorConfig prices"

        return QueryEvaluationResult(
            query_id=query_id,
            question=question,
            test_type=test_type,
            generated_answer=generated_answer,
            retrieved_chunks=retrieved_chunks,
            claims=claims,
            verifications=verifications,
            faithfulness_score=round(faithfulness, 4),
            hallucination_rate=round(hallucination_rate, 4),
            contradiction_rate=round(contra_rate, 4),
            claim_coverage=round(coverage, 4),
            citation_metrics=citation_metrics,
            retrieval_metrics=retrieval_metrics,
            abstained=abstained,
            correctly_abstained=correctly_abstained,
            retrieval_latency_ms=round(retrieval_latency_ms, 2),
            generation_latency_ms=round(generation_latency_ms, 2),
            verification_latency_ms=round(verif_latency_ms, 2),
            total_latency_ms=round(total_latency_ms, 2),
            token_count_prompt=prompt_tokens,
            token_count_completion=completion_tokens,
            estimated_cost_usd=None if cost_usd is None else round(cost_usd, 6),
            cost_pricing_source=pricing_source,
        )
