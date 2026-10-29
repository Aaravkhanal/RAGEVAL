"""Per-example and aggregate JSON for official metrics only."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional

from rageval.core.schemas import BenchmarkRunSummary, QueryEvaluationResult, TestType
from rageval.metrics.abstention import abstention_accuracy
from rageval.metrics.bootstrap import bootstrap_mean_ci
from rageval.metrics.registry import has_overall_score, official_metrics


def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def summarize_results(
    results: Iterable[QueryEvaluationResult],
    *,
    independent: bool = False,
) -> Dict[str, Any]:
    rows = list(results)
    faiths = [r.faithfulness_score for r in rows]
    unans = [r.test_type == TestType.UNANSWERABLE for r in rows]
    abstained = [r.abstained for r in rows]
    ems = [r.answer_em for r in rows if r.answer_em is not None]
    f1s = [r.answer_f1 for r in rows if r.answer_f1 is not None]
    costs = [r.estimated_cost_usd for r in rows if r.estimated_cost_usd is not None]
    support_prec = [
        r.citation_metrics.citation_support_precision for r in rows if r.citation_metrics
    ]
    payload = {
        "n": len(rows),
        "overall_score": None,
        "has_official_overall_score": has_overall_score(),
        "claim_support_rate": {
            "mean": _mean(faiths),
            "bootstrap": bootstrap_mean_ci(faiths, independent=independent) if faiths else None,
        },
        "unsupported_claim_rate": {"mean": _mean([r.hallucination_rate for r in rows])},
        "contradiction_rate": {"mean": _mean([r.contradiction_rate for r in rows])},
        "recall_at_5": {"mean": _mean([r.retrieval_metrics.recall_at_5 for r in rows])},
        "mrr": {"mean": _mean([r.retrieval_metrics.mrr for r in rows])},
        "citation_existence_precision": {
            "mean": _mean([r.citation_metrics.citation_precision for r in rows])
        },
        "citation_support_precision": {"mean": _mean(support_prec)},
        "citation_marker_recall": {
            "mean": _mean([r.citation_metrics.citation_recall for r in rows]),
            "legacy": True,
        },
        "answer_em": {"mean": _mean(ems)},
        "answer_f1": {"mean": _mean(f1s)},
        "abstention_accuracy": abstention_accuracy(abstained, unans) if rows else 1.0,
        "mean_latency_ms": _mean([r.total_latency_ms for r in rows]),
        "total_estimated_cost_usd": None if not costs else round(sum(costs), 6),
        "official_metric_names": [m.name for m in official_metrics()],
    }
    return payload


def robustness_by_scenario_type(
    results: Iterable[QueryEvaluationResult],
    *,
    independent: bool = False,
) -> Dict[str, Any]:
    """Named-metric means sliced by `scenario_type`. No overall score."""
    groups: Dict[str, List[QueryEvaluationResult]] = {}
    for result in results:
        key = result.scenario_type or "unknown"
        groups.setdefault(key, []).append(result)
    out: Dict[str, Any] = {}
    for key in sorted(groups):
        summary = summarize_results(groups[key], independent=independent)
        out[key] = {
            "n": summary["n"],
            "claim_support_rate": summary["claim_support_rate"]["mean"],
            "unsupported_claim_rate": summary["unsupported_claim_rate"]["mean"],
            "contradiction_rate": summary["contradiction_rate"]["mean"],
            "recall_at_5": summary["recall_at_5"]["mean"],
            "mrr": summary["mrr"]["mean"],
            "answer_em": summary["answer_em"]["mean"],
            "answer_f1": summary["answer_f1"]["mean"],
            "abstention_accuracy": summary["abstention_accuracy"],
            "citation_support_precision": summary["citation_support_precision"]["mean"],
        }
    return out


def write_metrics_bundle(
    run_dir: str,
    summaries: List[BenchmarkRunSummary],
    *,
    independent: bool = False,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """Write metrics.json (canonical), metrics/aggregate.json, and per_example.jsonl."""
    metrics_dir = os.path.join(run_dir, "metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    by_config = {}
    example_path = os.path.join(metrics_dir, "per_example.jsonl")
    with open(example_path, "w", encoding="utf-8") as f:
        for summary in summaries:
            by_config[summary.config_name] = summarize_results(
                summary.results, independent=independent
            )
            by_config[summary.config_name]["by_scenario"] = robustness_by_scenario_type(
                summary.results, independent=independent
            )
            for result in summary.results:
                record = {
                    "config_name": summary.config_name,
                    "query_id": result.query_id,
                    "test_type": result.test_type.value,
                    "claim_support_rate": result.faithfulness_score,
                    "unsupported_claim_rate": result.hallucination_rate,
                    "contradiction_rate": result.contradiction_rate,
                    "recall_at_5": result.retrieval_metrics.recall_at_5,
                    "mrr": result.retrieval_metrics.mrr,
                    "citation_existence_precision": result.citation_metrics.citation_precision,
                    "citation_support_precision": result.citation_metrics.citation_support_precision,
                    "citation_marker_recall": result.citation_metrics.citation_recall,
                    "answer_em": result.answer_em,
                    "answer_f1": result.answer_f1,
                    "abstained": result.abstained,
                    "scenario_type": result.scenario_type,
                    "total_latency_ms": result.total_latency_ms,
                    "estimated_cost_usd": result.estimated_cost_usd,
                }
                f.write(json.dumps(record) + "\n")
    aggregate = {
        "schema": "rageval.metrics.v1",
        "overall_score": None,
        "note": "No official composite ranking score. Compare named metrics only.",
        "independent_items_assumed": independent,
        "by_config": by_config,
    }
    if extra:
        for key, value in extra.items():
            if key not in aggregate:
                aggregate[key] = value
    agg_path = os.path.join(metrics_dir, "aggregate.json")
    with open(agg_path, "w", encoding="utf-8") as f:
        json.dump(aggregate, f, indent=2)
        f.write("\n")
    root_path = os.path.join(run_dir, "metrics.json")
    with open(root_path, "w", encoding="utf-8") as f:
        json.dump(aggregate, f, indent=2)
        f.write("\n")
    return root_path
