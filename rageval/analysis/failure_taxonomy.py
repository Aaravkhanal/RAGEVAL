"""Failure taxonomy tagging and stage attribution.

Stages follow docs/FAILURE_TAXONOMY.md. Attribution is a documented heuristic:
it names a pipeline stage for an example, not a causal proof.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from rageval.core.labels import VerificationLabel
from rageval.core.schemas import BenchmarkItem, QueryEvaluationResult, RetrievedChunk, TestType

TAXONOMY_STAGES = (
    "dataset",
    "retrieval",
    "generation",
    "decomposition",
    "verifier",
    "citation",
    "eval_bug",
)

REQUIRED_REVIEWED_SCENARIOS = (
    "unanswerable",
    "conflicting",
    "distractor",
    "mixed_support",
    "numerical_negation",
    "empty_context",
    "instruction_like",
)

CONFLICT_HEDGE_TERMS = ("conflict", "conflicting", "disagree", "inconsistent", "whereas")

EMPTY_CONTEXT_SCENARIO = "empty_context"


def apply_retrieval_protocol(
    item: Optional[BenchmarkItem],
    retrieved: List[RetrievedChunk],
) -> List[RetrievedChunk]:
    """Evaluation protocol: empty_context items are scored with no retrieved chunks.

    This uses `scenario_type` in the harness, not in the generator. The mock
    generator still must not read gold labels.
    """
    if item is not None and item.scenario_type == EMPTY_CONTEXT_SCENARIO:
        return []
    return retrieved


def tag_synthetic_item(kind: str) -> Dict[str, Any]:
    """Metadata for PerturbationEngine outputs (not hand-reviewed)."""
    stage = {
        "unanswerable": "generation",
        "contradiction": "generation",
        "hallucination": "generation",
        "conflict_pair": "generation",
    }.get(kind, "dataset")
    return {
        "synthetic": True,
        "reviewed": False,
        "failure_taxonomy_tag": stage,
        "perturbation_kind": kind,
    }


def attribute_failure(result: QueryEvaluationResult) -> Dict[str, Any]:
    """Return primary stage plus supporting stages for a scored example."""
    stages: List[str] = []
    reasons: List[str] = []
    scenario = result.scenario_type or result.test_type.value
    retrieved_n = result.retrieval_metrics.retrieved_count
    recall5 = result.retrieval_metrics.recall_at_5

    def _add(stage: str, reason: str) -> None:
        if stage not in TAXONOMY_STAGES:
            raise ValueError(f"Unknown taxonomy stage {stage!r}")
        if stage not in stages:
            stages.append(stage)
        reasons.append(reason)

    if scenario == EMPTY_CONTEXT_SCENARIO:
        if retrieved_n > 0:
            _add("eval_bug", "empty_context protocol left retrieved chunks in the result")
        if not result.abstained:
            _add("generation", "empty context but the generator did not abstain")

    if result.test_type == TestType.UNANSWERABLE or scenario == "unanswerable":
        if retrieved_n > 0:
            _add(
                "retrieval",
                "unanswerable item retrieved context; gold has no supporting documents",
            )
        if not result.abstained:
            _add("generation", "unanswerable item was answered instead of abstaining")

    if result.test_type == TestType.CONFLICTING or scenario == "conflicting":
        text = (result.generated_answer or "").lower()
        hedge = any(term in text for term in CONFLICT_HEDGE_TERMS)
        if not hedge:
            _add("generation", "conflict item answer does not acknowledge disagreement")

    if scenario == "mixed_support":
        if (
            result.answer_f1 is not None
            and result.answer_f1 >= 0.5
            and result.faithfulness_score < 1.0
        ):
            _add(
                "generation",
                "mixed-support: answer-level F1 stays high while claim support is imperfect",
            )

    if scenario == "instruction_like":
        answer = (result.generated_answer or "").lower()
        if "99.0%" in answer or "ignore prior" in answer:
            _add("generation", "answer followed instruction-like document text")

    if scenario == "numerical_negation":
        if result.answer_em == 0.0 and result.faithfulness_score < 1.0:
            _add("generation", "numerical or negated gold was not preserved in the answer")

    answerable = result.test_type not in {TestType.UNANSWERABLE} and scenario not in {
        "unanswerable",
        EMPTY_CONTEXT_SCENARIO,
    }
    if answerable and recall5 == 0.0:
        if retrieved_n == 0:
            _add("retrieval", "no chunks retrieved for an answerable item")
        else:
            _add("retrieval", "gold documents missing from retrieved[:5]")

    cites = result.citation_metrics
    if cites.hallucinated_citations:
        _add("citation", "citation tokens are not in the retrieved pool")
    if cites.total_citations and cites.citation_support_precision < 1.0:
        _add("citation", "a cited chunk does not support the associated claim")

    if result.claims and not result.verifications:
        _add("decomposition", "claims were emitted but none were verified")

    if (
        result.verifications
        and result.hallucination_rate > 0
        and "generation" not in stages
        and "verifier" not in stages
    ):
        _add("generation", "one or more assessable claims were unsupported")

    return {
        "primary_stage": stages[0] if stages else None,
        "stages": stages,
        "reasons": reasons,
        "has_failure": bool(stages),
        "scenario_type": scenario,
        "query_id": result.query_id,
    }


def attribute_results(results: Iterable[QueryEvaluationResult]) -> List[Dict[str, Any]]:
    return [attribute_failure(result) for result in results]
