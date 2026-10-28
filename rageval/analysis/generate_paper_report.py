"""Scientific benchmark execution and formal paper-style report generator."""

from __future__ import annotations
import os
import json
from rageval.dataset.loader import DatasetLoader
from rageval.benchmark.suite import BenchmarkSuite
from rageval.benchmark.reporter import BenchmarkReporter
from rageval.analysis.paper_plots import generate_all_paper_figures


def run_and_generate_paper_analysis(
    output_dir: str = "reports",
    dataset_id: str = "benchmark_v1",
    data_dir: str = "data",
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    loader = DatasetLoader(data_dir, dataset_id=dataset_id)
    corpus = loader.load_corpus()
    items = loader.load_benchmark("all")
    manifest = loader.load_manifest() or {}

    print(f"Loaded {len(corpus)} corpus documents and {len(items)} benchmark evaluation items.")
    suite = BenchmarkSuite()
    summaries = suite.run_suite(
        corpus,
        items,
        dataset_id=dataset_id,
        dataset_version=manifest.get("version"),
    )

    # 1. Export tables (CSV, JSON, LaTeX)
    BenchmarkReporter.export(summaries, output_dir=output_dir)

    # 2. Generate scientific figures
    figures_dir = os.path.join(output_dir, "figures")
    fig_paths = generate_all_paper_figures(summaries, output_dir=figures_dir)

    # 3. Compile full paper analysis markdown
    df = BenchmarkReporter.to_dataframe(summaries)
    table_md = df.to_markdown(index=False)

    report_content = f"""# RAGeval run report

**Status:** auto-generated tables only. Narrative scientific findings are **pending** until a named experiment run is analyzed in Phase 8.

This report must not claim retrieval or faithfulness improvements unless those differences appear in the table below.

---

## Ablation table

{table_md}

---

## Notes

- Default generation is a **blinded mock** that copies retrieved sentences. It is not a production LLM.
- Dataset: `{dataset_id}` ({len(corpus)} documents, {len(items)} items).
- Cost is omitted unless explicit pricing is configured.
- Compare configurations using the table, not canned commentary.

## Figures

- Figure 1: `figures/fig1_pareto_latency_faithfulness.png`
- Figure 2: `figures/fig2_claim_attribution_breakdown.png`
- Figure 3: `figures/fig3_retrieval_recall_mrr.png`
- Figure 4: `figures/fig4_adversarial_abstention.png`
"""

    report_path = os.path.join(output_dir, "paper_analysis.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"[RAGeval] Paper report generated at: {report_path}")
    return report_path


if __name__ == "__main__":
    run_and_generate_paper_analysis("reports")
