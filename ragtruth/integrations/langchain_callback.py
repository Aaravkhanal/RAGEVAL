"""LangChain callback integration for RAGTruth claim evaluation."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from ragtruth.core.schemas import Chunk, RetrievedChunk, QueryEvaluationResult
from ragtruth.evaluator.evaluator import RAGTruthEvaluator


class RAGTruthLangChainCallback:
    """Callback handler that can be passed to LangChain chains, agents, or retrievers.

    Captures retrieved documents and generated LLM answers to run claim-level evaluation.
    """

    def __init__(self, evaluator: Optional[RAGTruthEvaluator] = None):
        self.evaluator = evaluator or RAGTruthEvaluator()
        self.last_query: str = ""
        self.last_contexts: List[str] = []
        self.last_evaluation: Optional[QueryEvaluationResult] = None

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        # Extract query text
        self.last_query = (
            inputs.get("query")
            or inputs.get("question")
            or inputs.get("input")
            or str(inputs)
        )
        self.last_contexts = []

    def on_retriever_end(self, documents: List[Any], **kwargs: Any) -> None:
        """Captures retrieved documents (extracting page_content)."""
        self.last_contexts = []
        for doc in documents:
            if hasattr(doc, "page_content"):
                self.last_contexts.append(doc.page_content)
            elif isinstance(doc, dict):
                self.last_contexts.append(doc.get("text") or doc.get("page_content") or str(doc))
            else:
                self.last_contexts.append(str(doc))

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Evaluates generated output upon chain completion."""
        answer = (
            outputs.get("result")
            or outputs.get("output")
            or outputs.get("answer")
            or str(outputs)
        )

        retrieved_chunks = [
            RetrievedChunk(
                chunk=Chunk(
                    id=f"lc_chk_{i}",
                    doc_id=f"lc_doc_{i}",
                    text=c,
                    chunk_index=i-1,
                    token_count=len(c.split()),
                    start_char=0,
                    end_char=len(c),
                ),
                score=1.0,
                rank=i,
                retrieval_method="langchain_retriever",
            )
            for i, c in enumerate(self.last_contexts, start=1)
        ]

        self.last_evaluation = self.evaluator.evaluate_query(
            question=self.last_query,
            generated_answer=str(answer),
            retrieved_chunks=retrieved_chunks,
        )
