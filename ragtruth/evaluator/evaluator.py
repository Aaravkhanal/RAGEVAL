"""Complete claim-level faithfulness and attribution evaluator orchestrator."""

from __future__ import annotations
import time
from typing import List, Optional
from ragtruth.core.schemas import (
    BenchmarkItem,
    RetrievedChunk,
    QueryEvaluationResult,
    VerificationLabel,
    TestType,
)
from ragtruth.core.config import EvaluatorConfig
from ragtruth.evaluator.decomposer import AtomicClaimDecomposer
from ragtruth.evaluator.citation_parser import CitationParser
from ragtruth.evaluator.nli_verifier import NLIVerifier
from ragtruth.evaluator.retrieval_metrics import RetrievalMetricsCalculator


class RAGTruthEvaluator:
    """Scientific evaluator that determines factual entailment at the atomic claim level,

    audits citations, and scores retrieval quality and adversarial robustness.
    """

    def __init__(self, config: Optional[EvaluatorConfig] = None):
        self.config = config or EvaluatorConfig()
        self.nli_verifier = NLIVerifier(self.config)

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

        # 1. Decompose answer into atomic claims
        claims = AtomicClaimDecomposer.decompose(generated_answer, retrieved_chunks)

        # 2. Audit citation precision and recall
        citation_metrics = CitationParser.audit_citations(generated_answer, retrieved_chunks)

        # 3. Verify each atomic claim with NLI
        verifications = []
        for claim in claims:
            verif = self.nli_verifier.verify_claim(claim, retrieved_chunks)
            verifications.append(verif)

        # 4. Compute claim-level aggregate rates
        total_claims = len(verifications)
        if total_claims > 0:
            entailed_count = sum(1 for v in verifications if v.label == VerificationLabel.ENTAILEMENT)
            neutral_count = sum(1 for v in verifications if v.label == VerificationLabel.NEUTRAL)
            contradiction_count = sum(1 for v in verifications if v.label == VerificationLabel.CONTRADICTION)

            faithfulness = entailed_count / total_claims
            hallucination_rate = neutral_count / total_claims
            contradiction_rate = contradiction_count / total_claims
        else:
            # Empty or zero-claim response
            faithfulness = 1.0 if not generated_answer.strip() else 0.0
            hallucination_rate = 0.0
            contradiction_rate = 0.0

        # 5. Check abstention behavior
        lower_ans = generated_answer.lower()
        abstained = any(
            term in lower_ans
            for term in [
                "do not have sufficient information",
                "cannot be answered",
                "insufficient context",
                "not enough information",
            ]
        )

        correctly_abstained: Optional[bool] = None
        if item:
            if item.expected_abstention:
                correctly_abstained = abstained
            else:
                correctly_abstained = not abstained

        # 6. Compute retrieval metrics
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

        # Cost estimation ($1.50 per 1M prompt tokens, $2.00 per 1M completion tokens)
        cost_usd = (prompt_tokens * 0.0000015) + (completion_tokens * 0.0000020)

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
            contradiction_rate=round(contradiction_rate, 4),
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
            estimated_cost_usd=round(cost_usd, 6),
        )
