"""Dataset profiler calculating vocabulary statistics, document lengths, and claim distributions."""

from __future__ import annotations
import re
from typing import List, Dict, Any
import numpy as np
from ragtruth.core.schemas import Document, BenchmarkItem, TestType


class DatasetProfiler:
    """Computes distribution statistics over the corpus and evaluation items."""

    @staticmethod
    def profile_corpus(documents: List[Document]) -> Dict[str, Any]:
        if not documents:
            return {"total_documents": 0}

        word_counts = [len(d.text.split()) for d in documents]
        domains: Dict[str, int] = {}
        vocab = set()

        for d in documents:
            domains[d.domain or "general"] = domains.get(d.domain or "general", 0) + 1
            vocab.update(re.findall(r"\w+", d.text.lower()))

        return {
            "total_documents": len(documents),
            "total_tokens": int(sum(word_counts)),
            "mean_doc_tokens": round(float(np.mean(word_counts)), 1),
            "max_doc_tokens": int(np.max(word_counts)),
            "min_doc_tokens": int(np.min(word_counts)),
            "vocabulary_size": len(vocab),
            "domain_breakdown": domains,
        }

    @staticmethod
    def profile_benchmark(items: List[BenchmarkItem]) -> Dict[str, Any]:
        if not items:
            return {"total_items": 0}

        type_counts: Dict[str, int] = {}
        for it in items:
            type_counts[it.test_type.value] = type_counts.get(it.test_type.value, 0) + 1

        claims_per_item = [len(it.gold_atomic_claims) for it in items if it.test_type == TestType.STANDARD]

        return {
            "total_items": len(items),
            "test_type_distribution": type_counts,
            "mean_gold_claims_per_standard_item": round(float(np.mean(claims_per_item)), 2) if claims_per_item else 0.0,
            "unanswerable_count": type_counts.get("unanswerable", 0),
            "conflicting_count": type_counts.get("conflicting", 0),
        }
