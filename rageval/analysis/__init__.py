"""RAGeval analysis and publication reporting package."""

from rageval.analysis.paper_plots import generate_all_paper_figures
from rageval.analysis.generate_paper_report import run_and_generate_paper_analysis
from rageval.analysis.failure_taxonomy import (
    REQUIRED_REVIEWED_SCENARIOS,
    TAXONOMY_STAGES,
    apply_retrieval_protocol,
    attribute_failure,
    attribute_results,
)

__all__ = [
    "generate_all_paper_figures",
    "run_and_generate_paper_analysis",
    "TAXONOMY_STAGES",
    "REQUIRED_REVIEWED_SCENARIOS",
    "apply_retrieval_protocol",
    "attribute_failure",
    "attribute_results",
]
