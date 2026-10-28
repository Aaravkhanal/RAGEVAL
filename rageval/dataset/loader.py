"""Dataset loader and corpus management utilities."""

from __future__ import annotations
import json
import os
from typing import List, Optional
from rageval.core.schemas import Document, BenchmarkItem
from rageval.dataset.generator import create_synthetic_benchmark, save_benchmark_data


class DatasetLoader:
    """Loads and caches corpus documents and benchmark evaluation items."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, "raw")
        self.gold_dir = os.path.join(data_dir, "gold")
        self.adv_dir = os.path.join(data_dir, "adversarial")

    def ensure_data_exists(self) -> None:
        corpus_path = os.path.join(self.raw_dir, "corpus.json")
        if not os.path.exists(corpus_path):
            save_benchmark_data(self.data_dir)

    def load_corpus(self) -> List[Document]:
        self.ensure_data_exists()
        corpus_path = os.path.join(self.raw_dir, "corpus.json")
        with open(corpus_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Document(**doc) for doc in data]

    def load_benchmark(self, split: str = "all") -> List[BenchmarkItem]:
        """Loads benchmark items: 'all', 'standard', or 'adversarial'."""
        self.ensure_data_exists()
        if split == "standard":
            path = os.path.join(self.gold_dir, "benchmark_standard.json")
        elif split == "adversarial":
            path = os.path.join(self.adv_dir, "benchmark_adversarial.json")
        else:
            path = os.path.join(self.gold_dir, "benchmark_all.json")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [BenchmarkItem(**item) for item in data]
