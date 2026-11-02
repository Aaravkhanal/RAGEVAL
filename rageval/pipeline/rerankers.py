"""Neural Cross-Encoder reranking for candidate passages."""

from __future__ import annotations
from typing import List, Optional
from sentence_transformers import CrossEncoder
from rageval.core.schemas import RetrievedChunk
from rageval.core.config import RerankerConfig


class CrossEncoderReranker:
    """Reranks retrieved candidate chunks using a trained cross-encoder model."""

    def __init__(self, config: Optional[RerankerConfig] = None):
        self.config = config or RerankerConfig()
        self.enabled = self.config.enabled
        self.model = None

        if self.enabled:
            self.model = CrossEncoder(self.config.model_name, device=self.config.device)

    def rerank(self, query: str, candidates: List[RetrievedChunk], top_k: Optional[int] = None) -> List[RetrievedChunk]:
        if not self.enabled or not self.model or not candidates:
            k = top_k or len(candidates)
            return candidates[:k]

        pairs = [[query, c.chunk.text] for c in candidates]
        scores = self.model.predict(pairs)

        # Sort candidates by neural cross-encoder score descending
        ranked_indices = sorted(range(len(scores)), key=lambda i: float(scores[i]), reverse=True)
        limit = top_k or self.config.top_k or len(candidates)

        reranked: List[RetrievedChunk] = []
        for rank, idx in enumerate(ranked_indices[:limit], start=1):
            orig = candidates[idx]
            reranked.append(
                RetrievedChunk(
                    chunk=orig.chunk,
                    score=float(scores[idx]),
                    rank=rank,
                    retrieval_method="cross_encoder_reranked",
                )
            )

        return reranked
