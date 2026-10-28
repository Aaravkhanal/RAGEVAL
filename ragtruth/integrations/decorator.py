"""Python function decorator for effortless RAG pipeline evaluation and tracing."""

from __future__ import annotations
import functools
import inspect
from typing import Callable, Any, Optional, List, Dict
from ragtruth.core.schemas import Chunk, RetrievedChunk, QueryEvaluationResult
from ragtruth.evaluator.evaluator import RAGTruthEvaluator


def monitor_rag(
    evaluator: Optional[RAGTruthEvaluator] = None,
    fail_on_hallucination: bool = False,
    hallucination_threshold: float = 0.50,
):
    """Decorator for production RAG functions. Automatically inspects inputs/outputs,

    extracts context chunks and answers, and runs atomic claim evaluation.
    
    Supports functions returning:
    - (answer, context_chunks)
    - dict with keys {"answer": "...", "contexts": [...]}
    - str (when contexts are provided in args/kwargs)
    """
    _evaluator = evaluator or RAGTruthEvaluator()

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Infer question from first positional argument or keyword
            sig = inspect.signature(func)
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            question = (
                bound.arguments.get("question")
                or bound.arguments.get("query")
                or (args[0] if args and isinstance(args[0], str) else "Query")
            )

            # Execute decorated function
            result = func(*args, **kwargs)

            # Unpack answer and context chunks
            answer = ""
            raw_contexts: List[str] = []

            if isinstance(result, tuple) and len(result) >= 2:
                answer = str(result[0])
                raw_contexts = [str(c) for c in result[1]]
            elif isinstance(result, dict):
                answer = str(result.get("answer") or result.get("output") or result.get("response") or "")
                raw_contexts = [str(c) for c in (result.get("contexts") or result.get("source_documents") or [])]
            elif isinstance(result, str):
                answer = result
                raw_contexts = kwargs.get("contexts") or kwargs.get("context_chunks") or []

            # Format chunks
            retrieved_chunks = [
                RetrievedChunk(
                    chunk=Chunk(
                        id=f"monitored_chk_{i}",
                        doc_id=f"monitored_doc_{i}",
                        text=c,
                        chunk_index=i-1,
                        token_count=len(c.split()),
                        start_char=0,
                        end_char=len(c),
                    ),
                    score=1.0,
                    rank=i,
                    retrieval_method="decorated_app",
                )
                for i, c in enumerate(raw_contexts, start=1)
            ]

            eval_res = _evaluator.evaluate_query(
                question=question,
                generated_answer=answer,
                retrieved_chunks=retrieved_chunks,
            )

            # Attach evaluation report to result
            if isinstance(result, dict):
                result["ragtruth_evaluation"] = eval_res
            elif hasattr(result, "__dict__"):
                result.ragtruth_evaluation = eval_res

            unfaithful_rate = eval_res.hallucination_rate + eval_res.contradiction_rate
            if fail_on_hallucination and (unfaithful_rate > hallucination_threshold or eval_res.contradiction_rate > 0.0):
                raise ValueError(
                    f"[RAGTruth Alert] Generation failed hallucination check! "
                    f"Unfaithful rate: {unfaithful_rate:.2%} (Threshold: {hallucination_threshold:.2%})"
                )

            return result

        return wrapper

    return decorator
