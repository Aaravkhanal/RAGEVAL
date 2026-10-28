"""FAISS vector indexing and dense nearest neighbor retrieval."""

from __future__ import annotations
from typing import List, Tuple
import faiss
import numpy as np
from ragtruth.core.schemas import Chunk, RetrievedChunk
from ragtruth.pipeline.embedders import SentenceTransformerEmbedder


class FAISSIndex:
    """FAISS-based dense vector index supporting FlatIP and HNSW."""

    def __init__(
        self,
        embedder: SentenceTransformerEmbedder,
        index_type: str = "FlatIP",
        hnsw_m: int = 32,
    ):
        self.embedder = embedder
        self.index_type = index_type
        self.hnsw_m = hnsw_m
        self.dimension = embedder.dimension
        self.chunks: List[Chunk] = []

        if index_type == "HNSW":
            self.index = faiss.IndexHNSWFlat(self.dimension, self.hnsw_m, faiss.METRIC_INNER_PRODUCT)
        else:
            self.index = faiss.IndexFlatIP(self.dimension)

    def build(self, chunks: List[Chunk]) -> None:
        self.chunks = chunks
        if not chunks:
            return

        texts = [c.text for c in chunks]
        embeddings = self.embedder.encode(texts)
        self.index.reset()
        self.index.add(embeddings)

    def search(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        if not self.chunks or self.index.ntotal == 0:
            return []

        query_vec = self.embedder.encode_query(query).reshape(1, -1)
        k = min(top_k, len(self.chunks))
        scores, indices = self.index.search(query_vec, k)

        retrieved: List[RetrievedChunk] = []
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0]), start=1):
            if idx < 0 or idx >= len(self.chunks):
                continue
            retrieved.append(
                RetrievedChunk(
                    chunk=self.chunks[idx],
                    score=float(score),
                    rank=rank,
                    retrieval_method="dense",
                )
            )

        return retrieved
