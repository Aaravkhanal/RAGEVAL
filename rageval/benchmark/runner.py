"""Benchmark execution engine for running RAG pipelines through evaluation suites."""

from __future__ import annotations
import numpy as np
from typing import List, Optional
from rageval.core.labels import VerificationLabel
from rageval.core.schemas import (
    Document,
    BenchmarkItem,
    BenchmarkRunSummary,
    QueryEvaluationResult,
    TestType,
)
from rageval.benchmark.run_store import git_commit
from rageval.metrics.aggregate import robustness_by_scenario_type
from rageval.pipeline.rag import RAGPipeline
from rageval.evaluator.evaluator import RAGEvalEvaluator


class BenchmarkRunner:
    """Executes a benchmark suite against a configured RAG pipeline."""

    def __init__(self, pipeline: RAGPipeline, evaluator: Optional[RAGEvalEvaluator] = None):
        self.pipeline = pipeline
        self.evaluator = evaluator or RAGEvalEvaluator(self.pipeline.config.evaluator)

    def run(
        self,
        documents: List[Document],
        benchmark_items: List[BenchmarkItem],
        dataset_id: Optional[str] = None,
        dataset_version: Optional[str] = None,
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
                mean_recall_at_5=None,
                mean_mrr=None,
                mean_latency_ms=0.0,
                p95_latency_ms=0.0,
                abstention_accuracy=0.0,
                conflicting_detection_rate=0.0,
                mean_answer_em=None,
                mean_answer_f1=None,
                mixed_support_n=0,
                mixed_support_mean_answer_f1=None,
                mixed_support_mean_faithfulness=None,
                robustness_by_scenario={},
                total_estimated_cost_usd=None,
                dataset_id=dataset_id,
                dataset_version=dataset_version,
                results=[],
            )

        faiths = [r.faithfulness_score for r in results]
        hallucs = [r.hallucination_rate for r in results]
        contras = [r.contradiction_rate for r in results]
        precisions = [r.citation_metrics.citation_precision for r in results]
        recalls = [r.citation_metrics.citation_recall for r in results]
        answerable_results = [r for r in results if r.retrieval_metrics.no_answer_empty_retrieval is None]
        r5s = [r.retrieval_metrics.recall_at_5 for r in answerable_results]
        mrrs = [r.retrieval_metrics.mrr for r in answerable_results]
        latencies = [r.total_latency_ms for r in results]
        costs = [r.estimated_cost_usd for r in results if r.estimated_cost_usd is not None]

        unans_results = [r for r in results if r.test_type == TestType.UNANSWERABLE]
        abstention_acc = (
            sum(1 for r in unans_results if r.correctly_abstained) / len(unans_results)
            if unans_results
            else 1.0
        )

        hedge_terms = ("conflict", "conflicting", "disagree", "inconsistent", "whereas")
        conflicting_results = [r for r in results if r.test_type == TestType.CONFLICTING]

        def _conflict_signal(result: QueryEvaluationResult) -> bool:
            text = result.generated_answer.lower()
            if any(term in text for term in hedge_terms):
                return True
            return any(v.label == VerificationLabel.CONTRADICTED for v in result.verifications)

        conflict_detected = (
            sum(1 for r in conflicting_results if _conflict_signal(r)) / len(conflicting_results)
            if conflicting_results
            else 1.0
        )

        ems = [r.answer_em for r in results if r.answer_em is not None]
        f1s = [r.answer_f1 for r in results if r.answer_f1 is not None]
        mixed = [r for r in results if r.scenario_type == "mixed_support"]
        mixed_f1 = [r.answer_f1 for r in mixed if r.answer_f1 is not None]
        mixed_faith = [r.faithfulness_score for r in mixed]

        return BenchmarkRunSummary(
            config_name=self.pipeline.config.name,
            total_queries=total,
            mean_faithfulness=round(float(np.mean(faiths)), 4),
            mean_hallucination_rate=round(float(np.mean(hallucs)), 4),
            mean_contradiction_rate=round(float(np.mean(contras)), 4),
            mean_citation_precision=round(float(np.mean(precisions)), 4),
            mean_citation_recall=round(float(np.mean(recalls)), 4),
            mean_recall_at_5=round(float(np.mean(r5s)), 4) if r5s else None,
            mean_mrr=round(float(np.mean(mrrs)), 4) if mrrs else None,
            mean_latency_ms=round(float(np.mean(latencies)), 2),
            p95_latency_ms=round(float(np.percentile(latencies, 95)), 2),
            abstention_accuracy=round(float(abstention_acc), 4),
            conflicting_detection_rate=round(float(conflict_detected), 4),
            mean_answer_em=None if not ems else round(float(np.mean(ems)), 4),
            mean_answer_f1=None if not f1s else round(float(np.mean(f1s)), 4),
            mixed_support_n=len(mixed),
            mixed_support_mean_answer_f1=None if not mixed_f1 else round(float(np.mean(mixed_f1)), 4),
            mixed_support_mean_faithfulness=None if not mixed_faith else round(float(np.mean(mixed_faith)), 4),
            robustness_by_scenario=robustness_by_scenario_type(results),
            total_estimated_cost_usd=None if not costs else round(float(sum(costs)), 6),
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            git_commit=git_commit(),
            results=results,
        )
