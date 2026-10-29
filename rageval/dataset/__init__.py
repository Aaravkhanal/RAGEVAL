"""RAGeval dataset package."""

from rageval.dataset.loader import DatasetLoader
from rageval.dataset.generator import create_synthetic_benchmark, save_benchmark_data
from rageval.dataset.validator import validate_benchmark_integrity
from rageval.dataset.benchmark_v1 import build_benchmark, write_dataset
from rageval.dataset.pairs import PairedScenario, group_paired_items
from rageval.dataset.perturbations import PerturbationEngine

__all__ = [
    "DatasetLoader",
    "create_synthetic_benchmark",
    "save_benchmark_data",
    "validate_benchmark_integrity",
    "build_benchmark",
    "write_dataset",
    "PairedScenario",
    "group_paired_items",
    "PerturbationEngine",
]
