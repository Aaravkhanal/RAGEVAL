"""Publication-grade scientific visualizations for RAGTruth benchmark analysis."""

from __future__ import annotations
import os
from typing import List
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from ragtruth.core.schemas import BenchmarkRunSummary

# Configure research paper typography and aesthetics
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
})


def generate_all_paper_figures(summaries: List[BenchmarkRunSummary], output_dir: str = "reports/figures") -> List[str]:
    os.makedirs(output_dir, exist_ok=True)
    generated_paths = []

    configs = [s.config_name.replace("_", "\n") for s in summaries]
    short_configs = [s.config_name for s in summaries]
    faiths = [s.mean_faithfulness * 100 for s in summaries]
    hallucs = [s.mean_hallucination_rate * 100 for s in summaries]
    contras = [s.mean_contradiction_rate * 100 for s in summaries]
    recalls = [s.mean_recall_at_5 * 100 for s in summaries]
    mrrs = [s.mean_mrr for s in summaries]
    latencies = [s.mean_latency_ms for s in summaries]
    abstentions = [s.abstention_accuracy * 100 for s in summaries]

    # 1. Figure 1: Pareto Frontier: Latency vs. Claim Faithfulness
    fig, ax = plt.subplots(figsize=(8, 5))
    scatter = ax.scatter(latencies, faiths, s=140, c=recalls, cmap="viridis", edgecolors="black", linewidth=1.2, zorder=4)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Retrieval Recall@5 (%)")

    for i, txt in enumerate(short_configs):
        ax.annotate(
            txt,
            (latencies[i], faiths[i]),
            xytext=(6, 5),
            textcoords="offset points",
            fontsize=8.5,
            fontweight="medium",
        )

    ax.set_title("Pareto Analysis: System Latency vs. Answer Faithfulness", pad=12, fontweight="bold")
    ax.set_xlabel("Mean End-to-End Latency (ms)")
    ax.set_ylabel("Claim Faithfulness Rate (%)")
    ax.set_ylim(-5, 105)
    plt.tight_layout()
    p1 = os.path.join(output_dir, "fig1_pareto_latency_faithfulness.png")
    fig.savefig(p1, bbox_inches="tight")
    plt.close(fig)
    generated_paths.append(p1)

    # 2. Figure 2: Claim Attribution Breakdown (Stacked Bar)
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(configs))
    width = 0.55

    p_ent = ax.bar(x, faiths, width, label="Entailed (Supported)", color="#10b981", edgecolor="black", linewidth=0.8)
    p_neu = ax.bar(x, hallucs, width, bottom=faiths, label="Neutral (Unsupported / Hallucinated)", color="#f59e0b", edgecolor="black", linewidth=0.8)
    bottom_contra = [f + h for f, h in zip(faiths, hallucs)]
    p_con = ax.bar(x, contras, width, bottom=bottom_contra, label="Contradicted (Factual Conflict)", color="#ef4444", edgecolor="black", linewidth=0.8)

    ax.set_ylabel("Claim Proportion (%)")
    ax.set_title("Claim-Level Attribution Breakdown across RAG Pipeline Ablations", pad=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(configs, rotation=0, ha="center")
    ax.set_ylim(0, 105)
    ax.legend(loc="upper right", frameon=True)
    plt.tight_layout()
    p2 = os.path.join(output_dir, "fig2_claim_attribution_breakdown.png")
    fig.savefig(p2, bbox_inches="tight")
    plt.close(fig)
    generated_paths.append(p2)

    # 3. Figure 3: Information Retrieval Quality: Recall@5 & MRR
    fig, ax1 = plt.subplots(figsize=(9, 4.8))
    color1 = "#4f46e5"
    color2 = "#06b6d4"

    x_indices = np.arange(len(configs))
    bar_w = 0.35

    rects1 = ax1.bar(x_indices - bar_w/2, recalls, bar_w, label="Recall@5 (%)", color=color1, edgecolor="black", linewidth=0.8)
    ax2 = ax1.twinx()
    rects2 = ax2.bar(x_indices + bar_w/2, mrrs, bar_w, label="MRR", color=color2, edgecolor="black", linewidth=0.8)

    ax1.set_xlabel("Pipeline Configuration")
    ax1.set_ylabel("Recall@5 (%)", color=color1)
    ax2.set_ylabel("Mean Reciprocal Rank (MRR)", color=color2)
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels(configs, rotation=0, ha="center")
    ax1.set_ylim(0, 110)
    ax2.set_ylim(0, 1.1)

    ax1.set_title("Retrieval Quality Across Chunking and Indexing Strategies", pad=12, fontweight="bold")
    plt.tight_layout()
    p3 = os.path.join(output_dir, "fig3_retrieval_recall_mrr.png")
    fig.savefig(p3, bbox_inches="tight")
    plt.close(fig)
    generated_paths.append(p3)

    # 4. Figure 4: Adversarial Resilience (Abstention Rate on Unanswerables)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = ["#3b82f6" if a >= 80 else "#f97316" for a in abstentions]
    bars = ax.bar(configs, abstentions, color=colors, edgecolor="black", linewidth=0.8, width=0.5)

    for bar, val in zip(bars, abstentions):
        ax.text(bar.get_x() + bar.get_width()/2, val + 2, f"{val:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_ylabel("Abstention Accuracy (%)")
    ax.set_ylim(0, 115)
    ax.set_title("Adversarial Robustness: Correct Abstention on Unanswerable Queries", pad=12, fontweight="bold")
    plt.tight_layout()
    p4 = os.path.join(output_dir, "fig4_adversarial_abstention.png")
    fig.savefig(p4, bbox_inches="tight")
    plt.close(fig)
    generated_paths.append(p4)

    return generated_paths
