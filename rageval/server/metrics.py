"""Prometheus metrics exporter for production RAGeval evaluation monitoring."""

from __future__ import annotations
import threading
from typing import List, Dict, Any
import numpy as np
from rageval.core.schemas import QueryEvaluationResult


class MetricsCollector:
    """Thread-safe in-memory rolling metrics collector for Prometheus exposition."""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._lock = threading.Lock()
        self.total_evaluations = 0
        self.faithfulness_scores: List[float] = []
        self.hallucination_scores: List[float] = []
        self.contradiction_scores: List[float] = []
        self.citation_precisions: List[float] = []
        self.latencies_ms: List[float] = []

    def record_evaluation(self, res: QueryEvaluationResult) -> None:
        with self._lock:
            self.total_evaluations += 1
            self.faithfulness_scores.append(res.faithfulness_score)
            self.hallucination_scores.append(res.hallucination_rate)
            self.contradiction_scores.append(res.contradiction_rate)
            self.citation_precisions.append(res.citation_metrics.citation_precision)
            self.latencies_ms.append(res.total_latency_ms)

            # Cap rolling window
            if len(self.faithfulness_scores) > self.max_history:
                self.faithfulness_scores.pop(0)
                self.hallucination_scores.pop(0)
                self.contradiction_scores.pop(0)
                self.citation_precisions.pop(0)
                self.latencies_ms.pop(0)

    def generate_prometheus_metrics(self) -> str:
        with self._lock:
            total = self.total_evaluations
            mean_faith = float(np.mean(self.faithfulness_scores)) if self.faithfulness_scores else 1.0
            mean_halluc = float(np.mean(self.hallucination_scores)) if self.hallucination_scores else 0.0
            mean_contra = float(np.mean(self.contradiction_scores)) if self.contradiction_scores else 0.0
            mean_cite_p = float(np.mean(self.citation_precisions)) if self.citation_precisions else 1.0
            mean_lat = float(np.mean(self.latencies_ms)) if self.latencies_ms else 0.0
            p95_lat = float(np.percentile(self.latencies_ms, 95)) if self.latencies_ms else 0.0

        lines = [
            "# HELP rageval_evaluations_total Total number of RAG answers evaluated",
            "# TYPE rageval_evaluations_total counter",
            f"rageval_evaluations_total {total}",
            "",
            "# HELP rageval_faithfulness_ratio Rolling mean claim faithfulness ratio (0.0 to 1.0)",
            "# TYPE rageval_faithfulness_ratio gauge",
            f"rageval_faithfulness_ratio {mean_faith:.4f}",
            "",
            "# HELP rageval_hallucination_ratio Rolling mean hallucination rate (unsupported claims)",
            "# TYPE rageval_hallucination_ratio gauge",
            f"rageval_hallucination_ratio {mean_halluc:.4f}",
            "",
            "# HELP rageval_contradiction_ratio Rolling mean contradiction rate (factually refuted claims)",
            "# TYPE rageval_contradiction_ratio gauge",
            f"rageval_contradiction_ratio {mean_contra:.4f}",
            "",
            "# HELP rageval_citation_precision Rolling citation precision ratio",
            "# TYPE rageval_citation_precision gauge",
            f"rageval_citation_precision {mean_cite_p:.4f}",
            "",
            "# HELP rageval_latency_ms Mean total evaluation latency in milliseconds",
            "# TYPE rageval_latency_ms gauge",
            f"rageval_latency_ms {mean_lat:.2f}",
            "",
            "# HELP rageval_latency_p95_ms 95th percentile latency in milliseconds",
            "# TYPE rageval_latency_p95_ms gauge",
            f"rageval_latency_p95_ms {p95_lat:.2f}",
            "",
        ]
        return "\n".join(lines)


# Global singleton collector
global_metrics_collector = MetricsCollector()
