"""Named Phase 7 experiment slices: load YAML, run, write metrics.json."""

from __future__ import annotations

import glob
import os
from typing import List, Optional

import json

from rageval.analysis.significance import SignificanceAnalyzer
from rageval.benchmark.reporter import BenchmarkReporter
from rageval.benchmark.runner import BenchmarkRunner
from rageval.benchmark.run_store import create_run_dir, save_run
from rageval.benchmark.suite import BenchmarkSuite
from rageval.core.config import ExperimentSpec, experiment_spec_from_yaml
from rageval.core.schemas import BenchmarkRunSummary
from rageval.dataset.loader import DatasetLoader
from rageval.evaluator.evaluator import RAGEvalEvaluator
from rageval.metrics.aggregate import write_metrics_bundle
from rageval.pipeline.rag import RAGPipeline

EXPERIMENTS_DIR = os.path.join("configs", "experiments")


def list_experiment_paths(root: str = EXPERIMENTS_DIR) -> List[str]:
    return sorted(glob.glob(os.path.join(root, "[A-G]_*.yaml")))


def load_experiment(path: str) -> ExperimentSpec:
    return experiment_spec_from_yaml(path)


def require_opt_in_permission(
    *,
    opt_in: bool,
    resource_note: str = "",
    allow_opt_in: bool = False,
    name: str = "config",
) -> None:
    """Opt-in LLM / paid backends need an explicit CLI flag and a resource note."""
    if not opt_in:
        return
    if not allow_opt_in:
        raise RuntimeError(
            f"{name} is opt-in (live LLM or other paid/local model). "
            "Pass --allow-opt-in on the CLI. HTTP jobs never run opt-in configs. "
            "There is no mock fallback."
        )
    if not str(resource_note or "").strip():
        raise RuntimeError(
            f"{name} is opt-in and requires a non-empty resource_note "
            "before it can run."
        )


def run_experiment(
    spec: ExperimentSpec,
    *,
    data_dir: str = "data",
    output_root: str = "experiments/runs",
    max_items: Optional[int] = None,
    run_id: Optional[str] = None,
    existing_run_dir: Optional[str] = None,
    allow_opt_in: bool = False,
) -> str:
    """Run resolved pipelines. Analysis-only specs raise unless pipelines exist.

    CLI `main()` loads a gitignored `.env` before calling this. This function
    does not reload dotenv so tests that `delenv` keys stay isolated.
    """
    pipeline_opt_in = spec.opt_in or any(p.opt_in for p in spec.pipelines)
    note = spec.resource_note or next(
        (p.resource_note for p in spec.pipelines if p.resource_note), ""
    )
    require_opt_in_permission(
        opt_in=pipeline_opt_in,
        resource_note=note,
        allow_opt_in=allow_opt_in,
        name=f"Experiment {spec.experiment_id}",
    )
    if not spec.pipelines:
        raise ValueError(
            f"Experiment {spec.experiment_id} has no pipelines. "
            "Use tables_from_metrics for analysis-only slices."
        )
    loader = DatasetLoader(data_dir, dataset_id=spec.dataset_id)
    documents = loader.load_corpus()
    items = loader.load_benchmark(spec.split)
    if max_items is not None:
        items = items[: max(0, int(max_items))]
    manifest = loader.load_manifest() or {}
    dataset_version = manifest.get("version")
    if existing_run_dir:
        run_dir = existing_run_dir
    else:
        run_dir = create_run_dir(output_root, run_id=run_id)
    suite = BenchmarkSuite(spec.pipelines)
    summaries = suite.run_suite(
        documents,
        items,
        dataset_id=spec.dataset_id,
        dataset_version=dataset_version,
    )
    save_run(
        run_dir,
        summaries,
        extra_manifest={
            "experiment_id": spec.experiment_id,
            "label": spec.label,
            "title": spec.title,
            "family": spec.family,
            "data_dir": data_dir,
            "dataset_id": spec.dataset_id,
            "dataset_version": dataset_version,
            "split": spec.split,
            "n_documents": len(documents),
            "n_items": len(items),
            "resource_note": spec.resource_note,
            "max_items": max_items,
        },
        pipeline_configs=spec.pipelines,
        label=spec.label,
        experiment_id=spec.experiment_id,
    )
    return run_dir


def dry_run_two_configs(
    documents,
    items,
    configs,
    *,
    output_root: str,
    dataset_id: str = "smoke_v1",
    dataset_version: str = "1.0.0",
    run_id: str = "dry_run",
) -> str:
    """1-item × 2-config dry run used in tests. Does not overwrite completed runs."""
    if len(configs) != 2:
        raise ValueError("dry_run_two_configs expects exactly two pipeline configs")
    if len(items) != 1:
        raise ValueError("dry_run_two_configs expects exactly one benchmark item")
    run_dir = create_run_dir(output_root, run_id=run_id)
    summaries = []
    for cfg in configs:
        pipeline = RAGPipeline(cfg)
        evaluator = RAGEvalEvaluator(cfg.evaluator)
        runner = BenchmarkRunner(pipeline, evaluator=evaluator)
        summaries.append(
            runner.run(
                documents,
                items,
                dataset_id=dataset_id,
                dataset_version=dataset_version,
            )
        )
    save_run(
        run_dir,
        summaries,
        extra_manifest={
            "experiment_id": "dry_run",
            "label": "pilot",
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
            "n_items": 1,
            "n_configs": 2,
        },
        pipeline_configs=configs,
        label="pilot",
        experiment_id="dry_run",
    )
    return run_dir


def export_tables_from_summaries_json(
    summaries_path: str,
    output_dir: str,
    *,
    extra: Optional[dict] = None,
    baseline_name: str = "Dense_Chunk256_Baseline",
) -> str:
    """Write metrics.json + labeled tables from a completed summaries.json."""
    with open(summaries_path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    summaries = [BenchmarkRunSummary.model_validate(row) for row in rows]
    os.makedirs(output_dir, exist_ok=True)
    metrics_path = write_metrics_bundle(
        output_dir, summaries, independent=False, extra=extra or {}
    )
    metrics = BenchmarkReporter.load_metrics(metrics_path)
    BenchmarkReporter.export_from_metrics(metrics, output_dir, stem="table")
    with open(os.path.join(output_dir, "G_claim_vs_answer.md"), "w", encoding="utf-8") as f:
        f.write(BenchmarkReporter.claim_vs_answer_markdown(metrics))
    by_name = {s.config_name: s for s in summaries}
    comparisons = []
    if baseline_name in by_name:
        for name, summary in by_name.items():
            if name == baseline_name:
                continue
            metric_names = ("faithfulness", "recall", "evidence_recall") if (extra or {}).get("experiment_id") == "A_chunk" else ("faithfulness", "recall")
            for metric in metric_names:
                comparisons.append(
                    SignificanceAnalyzer.compare_runs(
                        by_name[baseline_name], summary, metric=metric
                    )
                )
    with open(os.path.join(output_dir, "significance.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "baseline": baseline_name,
                "note": (
                    "Confirmatory tests require n>=30 i.i.d. items. "
                    "Items that share documents are not i.i.d.; is_significant stays false."
                ),
                "comparisons": comparisons,
            },
            f,
            indent=2,
        )
        f.write("\n")
    return metrics_path
