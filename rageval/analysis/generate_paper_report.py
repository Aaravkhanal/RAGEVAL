"""Write paper-style tables from metrics.json. Does not invent findings."""

from __future__ import annotations

import json
import os
from typing import Optional

from rageval.benchmark.reporter import BenchmarkReporter
from rageval.dataset.loader import DatasetLoader


def run_and_generate_paper_analysis(
    output_dir: str = "reports",
    dataset_id: str = "benchmark_v1",
    data_dir: str = "data",
    metrics_path: Optional[str] = None,
    run_dir: Optional[str] = None,
) -> str:
    """Prefer an existing metrics.json. Re-running the suite is opt-in via no metrics path.

    Passing metrics_path or run_dir writes tables only. That is the Phase 7 path.
    """
    os.makedirs(output_dir, exist_ok=True)
    if run_dir and not metrics_path:
        metrics_path = os.path.join(run_dir, "metrics.json")
    if metrics_path:
        metrics = BenchmarkReporter.load_metrics(metrics_path)
        return write_report_from_metrics(metrics, output_dir)

    loader = DatasetLoader(data_dir, dataset_id=dataset_id)
    corpus = loader.load_corpus()
    items = loader.load_benchmark("all")
    raise RuntimeError(
        "rageval report no longer re-runs the ablation suite. Pass --metrics "
        "path/to/metrics.json or --run-dir experiments/runs/<id>. "
        f"Loaded {len(corpus)} docs / {len(items)} items for dataset {dataset_id!r} "
        "only to confirm the dataset exists."
    )


def write_report_from_metrics(metrics: dict, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    table_md = BenchmarkReporter.markdown_from_metrics(metrics)
    gap_md = BenchmarkReporter.claim_vs_answer_markdown(metrics)
    report_content = f"""# RAGeval run report

**Status:** tables generated from `metrics.json`. Narrative is `FINDINGS.md` for a named run, not this table file.

**Label:** `{metrics.get("label")}`. **Experiment:** `{metrics.get("experiment_id")}`.

This report must not claim retrieval or faithfulness improvements unless those differences appear in the table below and n is large enough for confirmatory tests (n≥30 i.i.d.).

---

{table_md}

---

{gap_md}

---

## Notes

- Default generation is a blinded mock that copies retrieved sentences.
- Cost is omitted unless explicit pricing is configured.
- Compare named metrics only. There is no overall score.
- Significance tests are diagnostic unless n≥30 i.i.d. (`underpowered=true` when items share documents).
"""
    report_path = os.path.join(output_dir, "paper_analysis.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    BenchmarkReporter.export_from_metrics(metrics, output_dir, stem="benchmark_summary")
    return report_path


def load_metrics_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Write tables from metrics.json")
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--output-dir", default="reports")
    args = parser.parse_args()
    print(run_and_generate_paper_analysis(output_dir=args.output_dir, metrics_path=args.metrics))
