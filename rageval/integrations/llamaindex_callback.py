"""LlamaIndex integration handler for RAGeval evaluation."""

from __future__ import annotations
from typing import Any, List, Optional
from rageval.core.schemas import Chunk, RetrievedChunk, QueryEvaluationResult
from rageval.evaluator.evaluator import RAGEvalEvaluator


class RAGEvalLlamaIndexHandler:
    """Interceptor for LlamaIndex query engine outputs."""

    def __init__(self, evaluator: Optional[RAGEvalEvaluator] = None):
        self.evaluator = evaluator or RAGEvalEvaluator()

    def evaluate_response(self, query: str, response: Any) -> QueryEvaluationResult:
        """Evaluates a LlamaIndex Response object containing source_nodes."""
        answer = str(getattr(response, "response", response))
        source_nodes = getattr(response, "source_nodes", [])

        contexts: List[str] = []
        for sn in source_nodes:
            if hasattr(sn, "node") and hasattr(sn.node, "get_content"):
                contexts.append(sn.node.get_content())
            elif hasattr(sn, "text"):
                contexts.append(sn.text)
            else:
                contexts.append(str(sn))

        retrieved_chunks = [
            RetrievedChunk(
                chunk=Chunk(
                    id=f"llama_chk_{i}",
                    doc_id=f"llama_doc_{i}",
                    text=c,
                    chunk_index=i-1,
                    token_count=len(c.split()),
                    start_char=0,
                    end_char=len(c),
                ),
                score=1.0,
                rank=i,
                retrieval_method="llamaindex_query_engine",
            )
            for i, c in enumerate(contexts, start=1)
        ]

        return self.evaluator.evaluate_query(
            question=query,
            generated_answer=answer,
            retrieved_chunks=retrieved_chunks,
        )
