"""FastAPI application: live claim audit, catalog, and durable experiment jobs."""

from __future__ import annotations

import os
import hmac
import json
from typing import Any, Dict, List, Literal, Optional, Union

from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from rageval import __version__
from rageval.core.assets import resolve_asset
from rageval.core.schemas import Chunk, QueryEvaluationResult, RetrievedChunk
from rageval.integrations.external import SCHEMA as SCORE_SCHEMA
from rageval.integrations.external import score_answer
from rageval.server.catalog import (
    data_dir,
    get_dataset,
    get_experiment,
    get_experiment_results,
    list_datasets,
    list_experiments,
    runs_root,
    table_from_metrics,
)
from rageval.server.jobs import enqueue_experiment, is_busy, list_named_configs
from rageval.server.metrics import global_metrics_collector
from rageval.server.runtime import (
    allowed_hosts,
    cors_allow_origins,
    get_evaluator,
    ProductionHeadersMiddleware,
    RateLimitMiddleware,
)
from rageval.server.streaming import StreamingVerificationSession

app = FastAPI(
    title="RAGeval Evaluation API",
    description=(
        "Claim-level faithfulness evaluation, dataset/run catalog, and a "
        "durable job queue for allowlisted experiment YAML names. "
        "POST /experiments returns 202 and never runs BenchmarkSuite on the "
        "request thread. POST /benchmark/run stays 410. Live /evaluate/answer "
        "and /score default to method=heuristic. This project is not "
        "Niu et al. 2024 RAGTruth."
    ),
    version=__version__,
)

_cors_origins, _cors_credentials = cors_allow_origins()
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ProductionHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts())

CLI_START = (
    "rageval experiment --config configs/experiments/C_retrieve.yaml "
    "--output-dir experiments/runs"
)
BENCHMARK_GONE = (
    "POST /benchmark/run is removed because it blocked the HTTP worker on a full "
    "ablation. Start a run with the CLI, then GET /experiments/{id}/results. "
    f"Example: {CLI_START}"
)


class LiveEvaluationRequest(BaseModel):
    question: str = Field(max_length=2048)
    answer: str = Field(max_length=16384)
    context_chunks: List[str] = Field(default_factory=list, max_length=10)
    method: Literal["heuristic", "nli"] = "heuristic"

    @field_validator("context_chunks")
    @classmethod
    def bound_chunks(cls, chunks: List[str]) -> List[str]:
        if any(len(chunk) > 8192 for chunk in chunks):
            raise ValueError("Each context chunk must be at most 8192 characters")
        return chunks


class LiveEvaluationResponse(BaseModel):
    evaluation: QueryEvaluationResult


class StreamEvaluationRequest(BaseModel):
    question: str = Field(max_length=2048)
    tokens: List[str] = Field(max_length=2048)
    context_chunks: List[str] = Field(default_factory=list, max_length=10)
    method: Literal["heuristic", "nli"] = "heuristic"

    @field_validator("tokens")
    @classmethod
    def bound_tokens(cls, tokens: List[str]) -> List[str]:
        if any(len(token) > 256 for token in tokens):
            raise ValueError("Each token must be at most 256 characters")
        return tokens

    @field_validator("context_chunks")
    @classmethod
    def bound_chunks(cls, chunks: List[str]) -> List[str]:
        return LiveEvaluationRequest.bound_chunks(chunks)


class ScoreRequest(BaseModel):
    question: str = Field(max_length=2048)
    answer: str = Field(max_length=16384)
    contexts: List[Union[str, Dict[str, Any]]] = Field(default_factory=list, max_length=10)
    method: Literal["heuristic", "nli"] = "heuristic"
    query_id: str = Field(default="live_query", max_length=128)

    @field_validator("contexts")
    @classmethod
    def bound_contexts(cls, contexts: List[Union[str, Dict[str, Any]]]) -> List[Union[str, Dict[str, Any]]]:
        if any(len(json.dumps(context)) > 8192 for context in contexts):
            raise ValueError("Each context must be at most 8192 JSON characters")
        return contexts


class StartExperimentRequest(BaseModel):
    config: str = Field(..., min_length=1, description="Allowlisted YAML stem under configs/experiments/")
    max_items: Optional[int] = Field(default=None, ge=1, le=32)
    allow_heavy: bool = False


def _http_evaluator(method: str):
    if method == "nli" and os.environ.get("RAGEVAL_ENABLE_HTTP_NLI", "0").lower() not in {"1", "true", "yes"}:
        raise HTTPException(status_code=403, detail="HTTP NLI is disabled; set RAGEVAL_ENABLE_HTTP_NLI=1 after provisioning the model")
    return get_evaluator(method)


def _health_payload() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "rageval",
        "version": __version__,
        "busy": is_busy(),
    }


@app.get("/health", tags=["meta"])
def health_check():
    """Liveness. Always 200 if this process can answer HTTP."""
    return _health_payload()


@app.get("/ready", tags=["meta"])
def ready_check():
    """Readiness. 200 when data exists and run storage is writable."""
    data_ok = os.path.isdir(data_dir())
    runs_ok = os.path.isdir(runs_root())
    ready = data_ok and runs_ok and os.access(runs_root(), os.W_OK)
    payload = {
        "status": "ready" if ready else "not_ready",
        "service": "rageval",
        "version": __version__,
        "busy": is_busy(),
        "data_ok": data_ok,
        "runs_ok": runs_ok,
    }
    if not ready:
        return JSONResponse(status_code=503, content=payload)
    return payload


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


@app.get("/experiment-configs", tags=["experiments"])
def experiment_configs():
    """Allowlisted YAML names. Heavy configs need allow_heavy on POST /experiments."""
    return {"configs": list_named_configs()}


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


@app.post("/experiments", tags=["experiments"], status_code=202)
def start_experiment(req: StartExperimentRequest, x_rageval_admin_token: Optional[str] = Header(default=None)):
    """Queue an allowlisted experiment. Default smoke; NLI/v1 needs allow_heavy."""
    expected = os.environ.get("RAGEVAL_ADMIN_TOKEN")
    if not expected:
        raise HTTPException(status_code=503, detail="Experiment jobs are disabled until RAGEVAL_ADMIN_TOKEN is configured")
    if not x_rageval_admin_token or not hmac.compare_digest(x_rageval_admin_token, expected):
        raise HTTPException(status_code=401, detail="Invalid experiment admin token")
    try:
        return enqueue_experiment(
            req.config,
            max_items=req.max_items,
            allow_heavy=req.allow_heavy,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown experiment config {req.config!r}",
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
    snapshot = resolve_asset(os.path.join("reports", "phase7", "v1_matrix", "metrics.json"))
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
        verifier=_http_evaluator(req.method).nli_verifier,
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
    """Decompose an answer and verify claims against caller-supplied context. Sync.

    Default method is heuristic so the dashboard does not download DeBERTa.
    Pass method=nli after explicitly enabling HTTP NLI and provisioning its model.
    """
    res = _http_evaluator(req.method).evaluate_query(
        question=req.question,
        generated_answer=req.answer,
        retrieved_chunks=_chunks_from_texts(req.context_chunks, "user_provided"),
    )
    global_metrics_collector.record_evaluation(res)
    return LiveEvaluationResponse(evaluation=res)


@app.post("/score", tags=["evaluate"])
def score_external(req: ScoreRequest):
    """HTTP surface for `rageval score`: question + contexts + answer in."""
    res = score_answer(
        req.question,
        req.answer,
        req.contexts,
        method=req.method,
        evaluator=_http_evaluator(req.method),
        query_id=req.query_id,
    )
    global_metrics_collector.record_evaluation(res)
    return {"schema": SCORE_SCHEMA, "evaluation": res}


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
