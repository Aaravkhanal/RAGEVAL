"""FastAPI application: live claim audit plus read-only experiment/dataset catalog."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rageval.core.config import EvaluatorConfig
from rageval.core.schemas import Chunk, QueryEvaluationResult, RetrievedChunk
from rageval.evaluator.evaluator import RAGEvalEvaluator
from rageval.server.catalog import (
    get_dataset,
    get_experiment,
    get_experiment_results,
    list_datasets,
    list_experiments,
    table_from_metrics,
)
from rageval.server.metrics import global_metrics_collector
from rageval.server.streaming import StreamingVerificationSession

app = FastAPI(
    title="RAGeval Evaluation API",
    description=(
        "Claim-level faithfulness evaluation and read-only access to datasets "
        "and experiment run folders. Full ablations are started from the CLI, "
        "not from HTTP. This project is not Niu et al. 2024 RAGTruth."
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_evaluator: Optional[RAGEvalEvaluator] = None
CLI_START = (
    "rageval experiment --config configs/experiments/C_retrieve.yaml "
    "--output-dir experiments/runs"
)
BENCHMARK_GONE = (
    "POST /benchmark/run is removed because it blocked the HTTP worker on a full "
    "ablation. Start a run with the CLI, then GET /experiments/{id}/results. "
    f"Example: {CLI_START}"
)


def get_evaluator() -> RAGEvalEvaluator:
    global _evaluator
    if _evaluator is None:
        _evaluator = RAGEvalEvaluator(EvaluatorConfig())
    return _evaluator


class LiveEvaluationRequest(BaseModel):
    question: str
    answer: str
    context_chunks: List[str] = Field(default_factory=list)


class LiveEvaluationResponse(BaseModel):
    evaluation: QueryEvaluationResult


class StreamEvaluationRequest(BaseModel):
    question: str
    tokens: List[str]
    context_chunks: List[str] = Field(default_factory=list)


@app.get("/health", tags=["meta"])
def health_check():
    return {"status": "ok", "service": "rageval"}


@app.get("/metrics", response_class=PlainTextResponse, tags=["meta"])
def prometheus_metrics():
    return global_metrics_collector.generate_prometheus_metrics()


@app.get("/datasets", tags=["datasets"])
def datasets_index():
    return {"datasets": list_datasets()}


@app.get("/datasets/{dataset_id}", tags=["datasets"])
def dataset_detail(dataset_id: str, include_items: bool = Query(default=True)):
    try:
        return get_dataset(dataset_id, include_items=include_items)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown dataset {dataset_id!r}")


@app.get("/experiments", tags=["experiments"])
def experiments_index():
    return {"experiments": list_experiments()}


@app.get("/experiments/{run_id}", tags=["experiments"])
def experiment_detail(run_id: str):
    try:
        return get_experiment(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown experiment {run_id!r}")


@app.get("/experiments/{run_id}/results", tags=["experiments"])
def experiment_results(run_id: str):
    try:
        return get_experiment_results(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"No metrics.json for experiment {run_id!r}",
        )


@app.post("/experiments", tags=["experiments"])
def start_experiment_cli_only():
    raise HTTPException(
        status_code=501,
        detail=(
            "Experiments are started from the CLI, not from HTTP. "
            f"Example: {CLI_START}"
        ),
    )


@app.post("/benchmark/run", tags=["experiments"], deprecated=True)
def run_benchmark_removed():
    raise HTTPException(status_code=410, detail=BENCHMARK_GONE)


@app.get("/metrics/summary", tags=["experiments"])
def get_metrics_summary() -> List[Dict[str, Any]]:
    """Table rows from the newest listed experiment. Empty if none exist."""
    experiments = list_experiments()
    for record in reversed(experiments):
        if not record.get("has_metrics"):
            continue
        try:
            payload = get_experiment_results(record["id"])
        except FileNotFoundError:
            continue
        return payload["table"]
    snapshot = os.path.join("reports", "phase7", "v1_matrix", "metrics.json")
    if os.path.isfile(snapshot):
        from rageval.benchmark.reporter import BenchmarkReporter

        return table_from_metrics(BenchmarkReporter.load_metrics(snapshot))
    return []


def _chunks_from_texts(texts: List[str], method: str) -> List[RetrievedChunk]:
    retrieved: List[RetrievedChunk] = []
    for idx, text in enumerate(texts, start=1):
        chunk = Chunk(
            id=f"chunk_{idx}",
            doc_id=f"doc_{idx}",
            text=text,
            chunk_index=idx - 1,
            token_count=len(text.split()),
            start_char=0,
            end_char=len(text),
        )
        retrieved.append(
            RetrievedChunk(
                chunk=chunk,
                score=1.0,
                rank=idx,
                retrieval_method=method,
            )
        )
    return retrieved


@app.post("/evaluate/stream", tags=["evaluate"])
def evaluate_stream(req: StreamEvaluationRequest):
    retrieved_chunks = _chunks_from_texts(req.context_chunks, "stream_context")
    session = StreamingVerificationSession(
        question=req.question,
        retrieved_chunks=retrieved_chunks,
        verifier=get_evaluator().nli_verifier,
    )
    events = []
    for tok in req.tokens:
        ev = session.process_token(tok)
        if ev:
            events.append(ev)
            if ev.get("guardrail_triggered"):
                break
    final_ev = session.flush()
    if final_ev:
        events.append(final_ev)
    return {"events": events, "total_verified_sentences": len(session.verified_sentences)}


@app.post("/evaluate/answer", response_model=LiveEvaluationResponse, tags=["evaluate"])
def evaluate_answer(req: LiveEvaluationRequest):
    """Decompose an answer and verify claims against caller-supplied context. Sync."""
    res = get_evaluator().evaluate_query(
        question=req.question,
        generated_answer=req.answer,
        retrieved_chunks=_chunks_from_texts(req.context_chunks, "user_provided"),
    )
    global_metrics_collector.record_evaluation(res)
    return LiveEvaluationResponse(evaluation=res)


static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse, tags=["meta"])
def index_page():
    index_html = os.path.join(static_dir, "index.html")
    if os.path.exists(index_html):
        with open(index_html, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>RAGeval API Server</h1><p>Visit /docs for OpenAPI documentation.</p>"
