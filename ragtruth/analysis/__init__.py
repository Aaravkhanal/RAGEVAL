"""RAGTruth analysis and publication reporting package."""

from ragtruth.analysis.paper_plots import generate_all_paper_figures
from ragtruth.analysis.generate_paper_report import run_and_generate_paper_analysis

__all__ = [
    "generate_all_paper_figures",
    "run_and_generate_paper_report",
]
