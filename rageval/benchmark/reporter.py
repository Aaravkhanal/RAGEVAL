"""Reporting and export utilities for benchmark ablation results."""

from __future__ import annotations
import json
import os
from typing import List
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
                "Abstention Acc": s.abstention_accuracy,
                "Latency (ms)": s.mean_latency_ms,
                "P95 Latency (ms)": s.p95_latency_ms,
                "Est. Cost ($)": s.total_estimated_cost_usd,
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
