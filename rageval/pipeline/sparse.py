"""BM25 sparse retrieval and Reciprocal Rank Fusion (RRF) hybrid search."""

from __future__ import annotations
import re
from rank_bm25 import BM25Plus
from rageval.core.schemas import Chunk, RetrievedChunk
from rageval.pipeline.indices import FAISSIndex


def tokenize_text(text: str) -> List[str]:
    """Simple alphanumeric lowercase tokenizer for BM25."""
    return re.findall(r"\w+", text.lower())


class BM25Retriever:
    """Sparse lexical retriever using BM25Plus for strictly non-negative term scoring."""

    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        self.corpus_tokens = [tokenize_text(c.text) for c in chunks]
        self.bm25 = BM25Plus(self.corpus_tokens) if self.corpus_tokens else None

    def search(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        if not self.bm25 or not self.chunks:
            return []

        query_tokens = tokenize_text(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        retrieved: List[RetrievedChunk] = []
        for rank, idx in enumerate(top_indices, start=1):
            retrieved.append(
                RetrievedChunk(
                    chunk=self.chunks[idx],
                    score=float(scores[idx]),
                    rank=rank,
                    retrieval_method="sparse_bm25",
                )
            )

        return retrieved


class HybridRetriever:
    """Combines dense (FAISS) and sparse (BM25) search using Reciprocal Rank Fusion (RRF)."""

    def __init__(self, faiss_index: FAISSIndex, bm25_retriever: BM25Retriever, rrf_k: int = 60):
        self.faiss_index = faiss_index
        self.bm25_retriever = bm25_retriever
        self.rrf_k = rrf_k

    def search(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        # Retrieve candidate pools from both dense and sparse
        pool_size = max(top_k * 2, 10)
        dense_results = self.faiss_index.search(query, top_k=pool_size)
        bm25_results = self.bm25_retriever.search(query, top_k=pool_size)

        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Chunk] = {}

        # Accumulate RRF scores: 1 / (k + rank)
        for r in dense_results:
            cid = r.chunk.id
            chunk_map[cid] = r.chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + r.rank))

        for r in bm25_results:
            cid = r.chunk.id
            chunk_map[cid] = r.chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + r.rank))

        # Sort by final RRF score descending
        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]

        fused_results: List[RetrievedChunk] = []
        for rank, cid in enumerate(sorted_cids, start=1):
            fused_results.append(
                RetrievedChunk(
                    chunk=chunk_map[cid],
                    score=float(rrf_scores[cid]),
                    rank=rank,
                    retrieval_method="hybrid_rrf",
                )
            )

        return fused_results
