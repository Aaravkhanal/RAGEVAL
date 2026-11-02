"""Matched retrieval matrix on the frozen, source-separated benchmark_v2 test split."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from pathlib import Path

from rageval.core.config import PipelineConfig
from rageval.dataset.loader import DatasetLoader
from rageval.metrics.retrieval import evidence_recall_at_k, recall_at_k
from rageval.pipeline.rag import RAGPipeline


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower), 3)


def run(output: Path) -> dict:
    loader = DatasetLoader("data", dataset_id="benchmark_v2")
    docs = loader.load_corpus()
    items = loader.load_benchmark("test")
    answerable = [item for item in items if item.gold_evidence_spans]
    rows = []
    matrix = [(method, size, None, False) for method in ("sparse", "dense", "hybrid") for size in (128, 256, 512)]
    matrix += [
        ("dense", 256, "sentence-transformers/all-mpnet-base-v2", False),
        ("hybrid", 256, None, True),
    ]
    for method, size, embedding_model, rerank in matrix:
            config = PipelineConfig.model_validate({
                "name": f"{method}_{size}" + ("_mpnet" if embedding_model else "") + ("_reranked" if rerank else ""),
                "chunker": {"strategy": "fixed", "chunk_size": size, "chunk_overlap": 32},
                "embedder": {"model_name": embedding_model or "sentence-transformers/all-MiniLM-L6-v2", "device": "cpu"},
                "retriever": {"method": method, "top_k": 5},
                "reranker": {"enabled": rerank, "top_k": 5},
                "generator": {"backend": "mock", "mock_mode": "faithful"},
                "evaluator": {"method": "heuristic"},
            })
            pipeline = RAGPipeline(config)
            start = time.perf_counter()
            pipeline.index(docs)
            index_ms = (time.perf_counter() - start) * 1000
            # Warm the query path before recording steady-state latency.
            pipeline.retrieve(answerable[0].question)
            latencies, doc_hits, span_hits = [], [], []
            for item in answerable:
                start = time.perf_counter()
                retrieved = pipeline.retrieve(item.question)
                latencies.append((time.perf_counter() - start) * 1000)
                doc_hits.append(recall_at_k(
                    [hit.chunk.doc_id for hit in retrieved],
                    {e.doc_id for e in item.gold_evidence_spans}, 5,
                ))
                span_hits.append(evidence_recall_at_k(
                    [hit.chunk.text for hit in retrieved],
                    [e.span for e in item.gold_evidence_spans], 5,
                ))
            rows.append({
                "name": config.name, "n": len(answerable), "n_chunks": len(pipeline.chunks),
                "index_ms_cold": round(index_ms, 3),
                "document_recall_at_5": round(statistics.mean(doc_hits), 4),
                "evidence_recall_at_5": round(statistics.mean(span_hits), 4),
                "warm_retrieval_ms": {"p50": percentile(latencies, .5), "p95": percentile(latencies, .95), "p99": percentile(latencies, .99)},
            })
            print(rows[-1], flush=True)
    report = {
        "dataset_id": "benchmark_v2", "version": "2.0.0", "split": "test",
        "machine": platform.platform(), "n_documents": len(docs),
        "n_test_items": len(items), "n_answerable": len(answerable),
        "note": "Single-author labels; retrieval-only matrix. Timing is local, sequential, after one warm query. No generation, NLI, or API cost included.",
        "configs": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("reports/phase8/retrieval_v2.json"))
    run(parser.parse_args().output)
