"""Benchmark execution engine for running RAG pipelines through evaluation suites."""

from __future__ import annotations
import numpy as np
from typing import List, Optional
from ragtruth.core.schemas import (
    Document,
    BenchmarkItem,
    BenchmarkRunSummary,
    QueryEvaluationResult,
    TestType,
)
from ragtruth.core.config import PipelineConfig
from ragtruth.pipeline.rag import RAGPipeline
from ragtruth.evaluator.evaluator import RAGTruthEvaluator


class BenchmarkRunner:
    """Executes a benchmark suite against a configured RAG pipeline."""

    def __init__(self, pipeline: RAGPipeline, evaluator: Optional[RAGTruthEvaluator] = None):
        self.pipeline = pipeline
        self.evaluator = evaluator or RAGTruthEvaluator(self.pipeline.config.evaluator)

    def run(
        self,
        documents: List[Document],
        benchmark_items: List[BenchmarkItem],
    ) -> BenchmarkRunSummary:
        # 1. Index corpus
        self.pipeline.index(documents)

        # 2. Iterate through benchmark items
        results: List[QueryEvaluationResult] = []

        for item in benchmark_items:
            # Query pipeline
            answer, retrieved_chunks, ret_ms, gen_ms, p_tok, c_tok = self.pipeline.query(
                question=item.question,
                item=item,
            )

            # Evaluate query
            eval_res = self.evaluator.evaluate_query(
                question=item.question,
                generated_answer=answer,
                retrieved_chunks=retrieved_chunks,
                item=item,
                retrieval_latency_ms=ret_ms,
                generation_latency_ms=gen_ms,
                prompt_tokens=p_tok,
                completion_tokens=c_tok,
            )
            results.append(eval_res)

        # 3. Aggregate statistics
        total = len(results)
        if total == 0:
            return BenchmarkRunSummary(
                config_name=self.pipeline.config.name,
                total_queries=0,
                mean_faithfulness=0.0,
                mean_hallucination_rate=0.0,
                mean_contradiction_rate=0.0,
                mean_citation_precision=0.0,
                mean_citation_recall=0.0,
                mean_recall_at_5=0.0,
                mean_mrr=0.0,
                mean_latency_ms=0.0,
                p95_latency_ms=0.0,
                abstention_accuracy=0.0,
                conflicting_detection_rate=0.0,
                total_estimated_cost_usd=0.0,
                results=[],
            )

        faiths = [r.faithfulness_score for r in results]
        hallucs = [r.hallucination_rate for r in results]
        contras = [r.contradiction_rate for r in results]
        precisions = [r.citation_metrics.citation_precision for r in results]
        recalls = [r.citation_metrics.citation_recall for r in results]
        r5s = [r.retrieval_metrics.recall_at_5 for r in results]
        mrrs = [r.retrieval_metrics.mrr for r in results]
        latencies = [r.total_latency_ms for r in results]
        costs = [r.estimated_cost_usd for r in results]

        # Adversarial checks
        unans_results = [r for r in results if r.test_type == TestType.UNANSWERABLE]
        abstention_acc = (
            sum(1 for r in unans_results if r.correctly_abstained) / len(unans_results)
            if unans_results
            else 1.0
        )

        conflicting_results = [r for r in results if r.test_type == TestType.CONFLICTING]
        conflict_detected = (
            sum(1 for r in conflicting_results if "conflict" in r.generated_answer.lower() or len(r.claims) >= 2)
            / len(conflicting_results)
            if conflicting_results
            else 1.0
        )

        return BenchmarkRunSummary(
            config_name=self.pipeline.config.name,
            total_queries=total,
            mean_faithfulness=round(float(np.mean(faiths)), 4),
            mean_hallucination_rate=round(float(np.mean(hallucs)), 4),
            mean_contradiction_rate=round(float(np.mean(contras)), 4),
            mean_citation_precision=round(float(np.mean(precisions)), 4),
            mean_citation_recall=round(float(np.mean(recalls)), 4),
            mean_recall_at_5=round(float(np.mean(r5s)), 4),
            mean_mrr=round(float(np.mean(mrrs)), 4),
            mean_latency_ms=round(float(np.mean(latencies)), 2),
            p95_latency_ms=round(float(np.percentile(latencies, 95)), 2),
            abstention_accuracy=round(float(abstention_acc), 4),
            conflicting_detection_rate=round(float(conflict_detected), 4),
            total_estimated_cost_usd=round(float(sum(costs)), 6),
            results=results,
        )
