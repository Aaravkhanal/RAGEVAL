"""Reporting and export utilities for benchmark ablation results."""

from __future__ import annotations
import json
import os
from typing import Any, Dict, List
import pandas as pd
from rageval.core.schemas import BenchmarkRunSummary


class BenchmarkReporter:
    """Formats and exports benchmark results to CSV, JSON, Markdown, and LaTeX tables."""

    @staticmethod
    def to_dataframe(summaries: List[BenchmarkRunSummary]) -> pd.DataFrame:
        records = []
        for s in summaries:
            records.append({
                "Configuration": s.config_name,
                "Faithfulness": s.mean_faithfulness,
                "Hallucination Rate": s.mean_hallucination_rate,
                "Contradiction Rate": s.mean_contradiction_rate,
                "Citation Precision": s.mean_citation_precision,
                "Recall@5": s.mean_recall_at_5,
                "MRR": s.mean_mrr,
                "Answer EM": s.mean_answer_em,
                "Answer F1": s.mean_answer_f1,
                "Mixed-support n": s.mixed_support_n,
                "Mixed-support F1": s.mixed_support_mean_answer_f1,
                "Mixed-support Faithfulness": s.mixed_support_mean_faithfulness,
                "Abstention Acc": s.abstention_accuracy,
                "Latency (ms)": s.mean_latency_ms,
                "P95 Latency (ms)": s.p95_latency_ms,
                "Est. Cost ($)": s.total_estimated_cost_usd,
                "Dataset": s.dataset_id,
            })
        return pd.DataFrame(records)

    @staticmethod
    def export(summaries: List[BenchmarkRunSummary], output_dir: str = "reports") -> None:
        os.makedirs(output_dir, exist_ok=True)
        df = BenchmarkReporter.to_dataframe(summaries)

        # 1. Save CSV
        csv_path = os.path.join(output_dir, "benchmark_summary.csv")
        df.to_csv(csv_path, index=False)

        # 2. Save JSON
        json_path = os.path.join(output_dir, "benchmark_detailed.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump([s.model_dump() for s in summaries], f, indent=2)

        # 3. Save Markdown Table
        md_path = os.path.join(output_dir, "benchmark_summary.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# RAGeval Ablation Benchmark Results\n\n")
            f.write(df.to_markdown(index=False))
            f.write("\n")

        # 4. Save LaTeX Table
        latex_path = os.path.join(output_dir, "benchmark_table.tex")
        with open(latex_path, "w", encoding="utf-8") as f:
            f.write("% Auto-generated RAGeval Benchmark LaTeX Table\n")
            f.write(df.to_latex(index=False, float_format="%.3f"))

        print(f"[BenchmarkReporter] Reports exported to: {output_dir}/")

    @staticmethod
    def dataframe_from_metrics(metrics: Dict[str, Any]) -> pd.DataFrame:
        rows = []
        for name, block in (metrics.get("by_config") or {}).items():
            mixed = (block.get("by_scenario") or {}).get("mixed_support") or {}
            rows.append(
                {
                    "Configuration": name,
                    "claim_support_rate": (block.get("claim_support_rate") or {}).get("mean"),
                    "unsupported_claim_rate": (block.get("unsupported_claim_rate") or {}).get("mean"),
                    "contradiction_rate": (block.get("contradiction_rate") or {}).get("mean"),
                    "recall_at_5": (block.get("recall_at_5") or {}).get("mean"),
                    "mrr": (block.get("mrr") or {}).get("mean"),
                    "answer_em": (block.get("answer_em") or {}).get("mean"),
                    "answer_f1": (block.get("answer_f1") or {}).get("mean"),
                    "abstention_accuracy": block.get("abstention_accuracy"),
                    "mixed_support_n": mixed.get("n"),
                    "mixed_support_f1": mixed.get("answer_f1"),
                    "mixed_support_claim_support": mixed.get("claim_support_rate"),
                    "n": block.get("n"),
                }
            )
        return pd.DataFrame(rows)

    @staticmethod
    def markdown_from_metrics(metrics: Dict[str, Any]) -> str:
        label = metrics.get("label") or "pilot"
        experiment_id = metrics.get("experiment_id") or "matrix"
        dataset_id = metrics.get("dataset_id") or ""
        version = metrics.get("dataset_version") or ""
        n_items = metrics.get("n_items")
        df = BenchmarkReporter.dataframe_from_metrics(metrics)
        heading = f"# RAGeval {label} matrix"
        lines = [
            heading,
            "",
            f"**Label:** `{label}` (not a confirmatory ranking).",
            f"**Experiment:** `{experiment_id}`.",
            f"**Dataset:** `{dataset_id}` {version}, n={n_items}.",
            "",
            "Tables are generated from `metrics.json`. There is no overall score.",
            "Do not read small-n differences as retrieval or faithfulness improvements.",
            "",
        ]
        if df.empty:
            lines.append("_No by_config rows in metrics.json._")
        else:
            lines.append(df.to_markdown(index=False))
        note = metrics.get("source_note")
        if note:
            lines.extend(["", note])
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def export_from_metrics(
        metrics: Dict[str, Any],
        output_dir: str,
        *,
        stem: str = "table",
    ) -> str:
        os.makedirs(output_dir, exist_ok=True)
        md = BenchmarkReporter.markdown_from_metrics(metrics)
        md_path = os.path.join(output_dir, f"{stem}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        df = BenchmarkReporter.dataframe_from_metrics(metrics)
        df.to_csv(os.path.join(output_dir, f"{stem}.csv"), index=False)
        with open(os.path.join(output_dir, "metrics.json"), "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
            f.write("\n")
        return md_path

    @staticmethod
    def load_metrics(path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def claim_vs_answer_markdown(metrics: Dict[str, Any]) -> str:
        label = metrics.get("label") or "pilot"
        lines = [
            f"# RAGeval {label} claim-level vs answer-level (mixed-support)",
            "",
            "Slice: `scenario_type=mixed_support`. Gold answers are fully supported; "
            "token F1 can stay high while claim support is mixed (RQ3).",
            "",
            "| Configuration | mixed n | answer F1 | claim support rate |",
            "| --- | ---: | ---: | ---: |",
        ]
        for name, block in (metrics.get("by_config") or {}).items():
            mixed = (block.get("by_scenario") or {}).get("mixed_support") or {}
            if not mixed:
                continue
            lines.append(
                f"| {name} | {mixed.get('n')} | {mixed.get('answer_f1')} | "
                f"{mixed.get('claim_support_rate')} |"
            )
        lines.extend(
            [
                "",
                "No overall score. n on this slice is 4 in the recorded v1.0.0 run.",
                "",
            ]
        )
        return "\n".join(lines)
