"""FastAPI application entrypoint for RAGTruth live evaluation and benchmark reporting."""

from __future__ import annotations
import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

from ragtruth.core.schemas import (
    Document,
    Chunk,
    RetrievedChunk,
    BenchmarkItem,
    QueryEvaluationResult,
    BenchmarkRunSummary,
)
from ragtruth.core.config import EvaluatorConfig, PipelineConfig
from ragtruth.evaluator.evaluator import RAGTruthEvaluator
from ragtruth.dataset.loader import DatasetLoader
from ragtruth.benchmark.suite import BenchmarkSuite
from ragtruth.benchmark.reporter import BenchmarkReporter

app = FastAPI(
    title="RAGTruth Evaluation API",
    description="Research-grade benchmark and claim-level faithfulness evaluation service for RAG.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent evaluator instance
evaluator = RAGTruthEvaluator(EvaluatorConfig())
dataset_loader = DatasetLoader("data")
latest_benchmark_summaries: List[BenchmarkRunSummary] = []


class LiveEvaluationRequest(BaseModel):
    question: str
    answer: str
    context_chunks: List[str] = Field(default_factory=list)


class LiveEvaluationResponse(BaseModel):
    evaluation: QueryEvaluationResult


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ragtruth"}


@app.post("/evaluate/answer", response_model=LiveEvaluationResponse)
def evaluate_answer(req: LiveEvaluationRequest):
    """Decomposes an answer into atomic claims and verifies them against the provided context chunks."""
    retrieved_chunks: List[RetrievedChunk] = []
    for idx, text in enumerate(req.context_chunks, start=1):
        chunk = Chunk(
            id=f"chunk_{idx}",
            doc_id=f"doc_{idx}",
            text=text,
            chunk_index=idx - 1,
            token_count=len(text.split()),
            start_char=0,
            end_char=len(text),
        )
        retrieved_chunks.append(
            RetrievedChunk(
                chunk=chunk,
                score=1.0,
                rank=idx,
                retrieval_method="user_provided",
            )
        )

    res = evaluator.evaluate_query(
        question=req.question,
        generated_answer=req.answer,
        retrieved_chunks=retrieved_chunks,
    )
    return LiveEvaluationResponse(evaluation=res)


@app.post("/benchmark/run", response_model=List[BenchmarkRunSummary])
def run_benchmark():
    """Runs the full ablation benchmark suite and updates cached summaries."""
    global latest_benchmark_summaries
    corpus = dataset_loader.load_corpus()
    benchmark_items = dataset_loader.load_benchmark("all")

    suite = BenchmarkSuite()
    latest_benchmark_summaries = suite.run_suite(corpus, benchmark_items)
    BenchmarkReporter.export(latest_benchmark_summaries, output_dir="reports")
    return latest_benchmark_summaries


@app.get("/metrics/summary")
def get_metrics_summary():
    """Returns the latest ablation run metrics as tabular records."""
    global latest_benchmark_summaries
    if not latest_benchmark_summaries:
        # Check if saved json exists
        summary_path = os.path.join("reports", "benchmark_detailed.json")
        if os.path.exists(summary_path):
            import json
            with open(summary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        return []
    return [s.model_dump() for s in latest_benchmark_summaries]


# Mount static assets directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
def index_page():
    index_html = os.path.join(static_dir, "index.html")
    if os.path.exists(index_html):
        with open(index_html, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>RAGTruth API Server</h1><p>Visit /docs for OpenAPI swagger documentation.</p>"
