"""Dataset loader and corpus management utilities."""

from __future__ import annotations

import json
import os
from typing import List, Optional

from rageval.core.schemas import Document, BenchmarkItem
from rageval.dataset.generator import save_benchmark_data


SMOKE_DATASET_ID = "smoke_v1"
DEFAULT_DATASET_ID = SMOKE_DATASET_ID

_LEGACY_SMOKE_PATHS = {
    "corpus": ("raw", "corpus.json"),
    "all": ("gold", "benchmark_all.json"),
    "standard": ("gold", "benchmark_standard.json"),
    "adversarial": ("adversarial", "benchmark_adversarial.json"),
}


class DatasetLoader:
    """Loads and caches corpus documents and benchmark evaluation items."""

    def __init__(self, data_dir: str = "data", dataset_id: str = DEFAULT_DATASET_ID):
        self.data_dir = data_dir
        self.dataset_id = dataset_id
        self.raw_dir = os.path.join(data_dir, "raw")
        self.gold_dir = os.path.join(data_dir, "gold")
        self.adv_dir = os.path.join(data_dir, "adversarial")
        self.dataset_dir = os.path.join(data_dir, "datasets", dataset_id)

    def _legacy_smoke(self) -> bool:
        return self.dataset_id == SMOKE_DATASET_ID

    def ensure_data_exists(self) -> None:
        if not self._legacy_smoke():
            return
        corpus_path = os.path.join(self.raw_dir, "corpus.json")
        if not os.path.exists(corpus_path):
            save_benchmark_data(self.data_dir)

    def _path(self, kind: str) -> str:
        if self._legacy_smoke():
            parts = _LEGACY_SMOKE_PATHS[kind]
            return os.path.join(self.data_dir, *parts)
        filename = {
            "corpus": "corpus.json",
            "all": "items.json",
            "standard": "items_standard.json",
            "adversarial": "items_adversarial.json",
            "dev": "items_dev.json",
            "test": "items_test.json",
        }[kind]
        return os.path.join(self.dataset_dir, filename)

    def load_corpus(self) -> List[Document]:
        self.ensure_data_exists()
        path = self._path("corpus")
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Corpus for dataset {self.dataset_id!r} not found at {path}"
            )
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Document(**doc) for doc in data]

    def load_benchmark(self, split: str = "all") -> List[BenchmarkItem]:
        """Loads benchmark items: 'all', 'standard', 'adversarial', 'dev', or 'test'."""
        self.ensure_data_exists()
        key = split if split in {"all", "standard", "adversarial", "dev", "test"} else "all"
        if key in {"dev", "test"} and self._legacy_smoke():
            items = self._read_items(self._path("all"))
            return [item for item in items if item.split == key] or items
        path = self._path(key)
        return self._read_items(path)

    def _read_items(self, path: str) -> List[BenchmarkItem]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Benchmark items for dataset {self.dataset_id!r} not found at {path}"
            )
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [BenchmarkItem(**item) for item in data]

    def load_manifest(self) -> Optional[dict]:
        path = os.path.join(self.data_dir, "manifests", f"{self.dataset_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
