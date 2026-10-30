"""Score a caller-supplied RAG answer against supplied chunks.

This is the external adapter: question + chunks + answer in, QueryEvaluationResult
out. It does not retrieve and does not call a generator. Gold labels never enter
the prompt because there is no prompt.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from rageval.core.config import EvaluatorConfig
from rageval.core.schemas import (
    BenchmarkItem,
    Chunk,
    QueryEvaluationResult,
    RetrievedChunk,
)
from rageval.evaluator.evaluator import RAGEvalEvaluator

SCHEMA = "rageval.external_score.v1"
ContextInput = Union[str, Dict[str, Any]]


def chunks_from_contexts(contexts: Sequence[ContextInput]) -> List[RetrievedChunk]:
    """Build RetrievedChunk rows from strings or {text, id, doc_id, score} maps."""
    rows: List[RetrievedChunk] = []
    for i, raw in enumerate(contexts, start=1):
        if isinstance(raw, str):
            text = raw
            chunk_id = f"ext_chk_{i}"
            doc_id = f"ext_doc_{i}"
            score = 1.0
        elif isinstance(raw, dict):
            text = str(raw.get("text") or raw.get("content") or raw.get("page_content") or "")
            chunk_id = str(raw.get("id") or raw.get("chunk_id") or f"ext_chk_{i}")
            doc_id = str(raw.get("doc_id") or raw.get("document_id") or f"ext_doc_{i}")
            score = float(raw.get("score") if raw.get("score") is not None else 1.0)
        else:
            raise TypeError(f"context[{i-1}] must be a string or object, got {type(raw).__name__}")
        rows.append(
            RetrievedChunk(
                chunk=Chunk(
                    id=chunk_id,
                    doc_id=doc_id,
                    text=text,
                    chunk_index=i - 1,
                    token_count=len(text.split()),
                    start_char=0,
                    end_char=len(text),
                ),
                score=score,
                rank=i,
                retrieval_method="external",
            )
        )
    return rows


def score_answer(
    question: str,
    answer: str,
    contexts: Sequence[ContextInput],
    *,
    method: str = "heuristic",
    evaluator: Optional[RAGEvalEvaluator] = None,
    query_id: str = "live_query",
    gold_answer: Optional[str] = None,
    expected_abstention: bool = False,
) -> QueryEvaluationResult:
    """Verify an already-generated answer against the chunks the RAG system used."""
    if method not in {"nli", "heuristic"}:
        raise ValueError(f"method must be 'nli' or 'heuristic', got {method!r}")
    ev = evaluator or RAGEvalEvaluator(EvaluatorConfig(method=method, allow_heuristic_fallback=False))
    item = None
    if gold_answer is not None or expected_abstention:
        item = BenchmarkItem(
            id=query_id,
            question=question,
            gold_answer=gold_answer,
            expected_abstention=expected_abstention,
            answerability="unanswerable" if expected_abstention else "answerable",
        )
    return ev.evaluate_query(
        question=question,
        generated_answer=answer,
        retrieved_chunks=chunks_from_contexts(contexts),
        item=item,
        query_id=query_id,
    )


def prediction_to_score_record(row: Dict[str, Any]) -> Dict[str, Any]:
    """Turn a run `predictions.jsonl` row into a `rageval score` record."""
    contexts = []
    for rc in row.get("retrieved_chunks") or []:
        if isinstance(rc, str):
            contexts.append(rc)
            continue
        if not isinstance(rc, dict):
            continue
        chunk = rc.get("chunk") if isinstance(rc.get("chunk"), dict) else rc
        contexts.append(
            {
                "id": chunk.get("id"),
                "doc_id": chunk.get("doc_id"),
                "text": chunk.get("text") or chunk.get("content") or "",
                "score": rc.get("score"),
            }
        )
    if not contexts:
        for key in ("contexts", "chunks", "context_chunks", "context"):
            if key in row:
                value = row[key]
                contexts = [value] if isinstance(value, str) else list(value or [])
                break
    return {
        "id": row.get("id") or row.get("query_id"),
        "question": row.get("question") or row.get("query"),
        "answer": row.get("answer") or row.get("generated_answer") or row.get("output"),
        "contexts": contexts,
        "gold_answer": row.get("gold_answer"),
        "expected_abstention": bool(row.get("expected_abstention") or False),
    }


def normalize_score_record(row: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(row, dict):
        raise TypeError("score record must be an object")
    if "retrieved_chunks" in row or "generated_answer" in row:
        return prediction_to_score_record(row)
    return row


def _contexts_from_record(row: Dict[str, Any]) -> List[Any]:
    for key in ("contexts", "chunks", "context_chunks", "context"):
        if key not in row:
            continue
        value = row[key]
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return value
        raise ValueError(f"{key} must be a string or list")
    raise ValueError("record needs contexts, chunks, context_chunks, or context")


def iter_score_records(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    stripped = text.strip()
    if not stripped:
        return
    if stripped.startswith("["):
        payload = json.loads(stripped)
        if not isinstance(payload, list):
            raise ValueError("JSON array expected")
        for row in payload:
            if not isinstance(row, dict):
                raise ValueError("each JSON array element must be an object")
            yield row
        return
    for line_no, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no} must be a JSON object")
        yield row


def score_records(
    records: Iterable[Dict[str, Any]],
    *,
    method: str = "heuristic",
    evaluator: Optional[RAGEvalEvaluator] = None,
) -> List[QueryEvaluationResult]:
    ev = evaluator or RAGEvalEvaluator(EvaluatorConfig(method=method, allow_heuristic_fallback=False))
    results: List[QueryEvaluationResult] = []
    for i, row in enumerate(records, start=1):
        row = normalize_score_record(row)
        question = row.get("question") or row.get("query")
        answer = row.get("answer") or row.get("generated_answer") or row.get("output")
        if not question:
            raise ValueError(f"record {i} missing question")
        if answer is None:
            raise ValueError(f"record {i} missing answer")
        query_id = str(row.get("id") or row.get("query_id") or f"ext_{i}")
        results.append(
            score_answer(
                str(question),
                str(answer),
                _contexts_from_record(row),
                method=method,
                evaluator=ev,
                query_id=query_id,
                gold_answer=row.get("gold_answer"),
                expected_abstention=bool(row.get("expected_abstention") or False),
            )
        )
    return results


def result_to_jsonable(result: QueryEvaluationResult) -> Dict[str, Any]:
    payload = result.model_dump(mode="json")
    payload["schema"] = SCHEMA
    return payload


def write_score_jsonl(results: Sequence[QueryEvaluationResult], path: str) -> str:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result_to_jsonable(result), ensure_ascii=False))
            f.write("\n")
    return path


def score_file(input_path: str, output_path: str, *, method: str = "heuristic") -> str:
    results = score_records(iter_score_records(input_path), method=method)
    return write_score_jsonl(results, output_path)
