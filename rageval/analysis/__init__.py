"""RAGeval analysis and publication reporting package."""

from rageval.analysis.generate_paper_report import run_and_generate_paper_analysis
from rageval.analysis.findings import assert_findings_text_allowed, write_findings
from rageval.analysis.failure_taxonomy import (
    REQUIRED_REVIEWED_SCENARIOS,
    TAXONOMY_STAGES,
    apply_retrieval_protocol,
    attribute_failure,
    attribute_results,
)


def generate_all_paper_figures(*args, **kwargs):
    from rageval.analysis.paper_plots import generate_all_paper_figures as _fn

    return _fn(*args, **kwargs)


def generate_figures_from_metrics(*args, **kwargs):
    from rageval.analysis.paper_plots import generate_figures_from_metrics as _fn

    return _fn(*args, **kwargs)


__all__ = [
    "generate_all_paper_figures",
    "generate_figures_from_metrics",
    "run_and_generate_paper_analysis",
    "write_findings",
    "assert_findings_text_allowed",
    "TAXONOMY_STAGES",
    "REQUIRED_REVIEWED_SCENARIOS",
    "apply_retrieval_protocol",
    "attribute_failure",
    "attribute_results",
]
