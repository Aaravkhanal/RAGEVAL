"""End-to-end RAG pipeline assembling chunking, vector indexing, hybrid search, reranking, and generation."""

from __future__ import annotations
import time
from typing import List, Optional, Tuple
from rageval.analysis.failure_taxonomy import apply_retrieval_protocol
from rageval.core.schemas import Document, Chunk, RetrievedChunk, BenchmarkItem
from rageval.core.config import PipelineConfig
from rageval.pipeline.chunkers import get_chunker
from rageval.pipeline.sparse import BM25Retriever, HybridRetriever
from rageval.pipeline.generator import get_generator, BaseGenerator


class RAGPipeline:
    """Configurable, modular RAG pipeline under test."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.chunker = get_chunker(self.config.chunker)
        self.embedder = None
        self.faiss_index = None
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.hybrid_retriever: Optional[HybridRetriever] = None
        self.reranker = None
        self.generator: BaseGenerator = get_generator(self.config.generator)
        self.documents: List[Document] = []
        self.chunks: List[Chunk] = []

    def _needs_dense(self) -> bool:
        return self.config.retriever.method in {"dense", "hybrid"}

    def _needs_sparse(self) -> bool:
        return self.config.retriever.method in {"sparse", "hybrid"}

    def index(self, documents: List[Document]) -> None:
        """Chunks documents and builds only the indices the retriever method needs."""
        self.documents = documents
        self.chunks = self.chunker.chunk_documents(documents)

        if self._needs_dense():
            from rageval.pipeline.embedders import SentenceTransformerEmbedder
            from rageval.pipeline.indices import FAISSIndex

            self.embedder = SentenceTransformerEmbedder(self.config.embedder)
            self.faiss_index = FAISSIndex(
                embedder=self.embedder,
                index_type=self.config.retriever.index_type,
            )
            self.faiss_index.build(self.chunks)

        if self._needs_sparse():
            self.bm25_retriever = BM25Retriever(self.chunks)

        if self.config.retriever.method == "hybrid" and self.faiss_index and self.bm25_retriever:
            self.hybrid_retriever = HybridRetriever(
                faiss_index=self.faiss_index,
                bm25_retriever=self.bm25_retriever,
                rrf_k=self.config.retriever.rrf_k,
            )

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[RetrievedChunk]:
        k = top_k or self.config.retriever.top_k
        method = self.config.retriever.method

        if method == "sparse":
            if not self.bm25_retriever:
                raise RuntimeError("Sparse retriever requested but BM25 index was not built.")
            candidates = self.bm25_retriever.search(query, top_k=k)
        elif method == "hybrid":
            if not self.hybrid_retriever:
                raise RuntimeError("Hybrid retriever requested but hybrid index was not built.")
            candidates = self.hybrid_retriever.search(query, top_k=k)
        else:
            if not self.faiss_index:
                raise RuntimeError("Dense retriever requested but FAISS index was not built.")
            candidates = self.faiss_index.search(query, top_k=k)

        # Apply reranking if configured
        if self.config.reranker.enabled:
            if self.reranker is None:
                from rageval.pipeline.rerankers import CrossEncoderReranker

                self.reranker = CrossEncoderReranker(self.config.reranker)
            candidates = self.reranker.rerank(query, candidates, top_k=self.config.reranker.top_k)

        return candidates

    def query(
        self,
        question: str,
        item: Optional[BenchmarkItem] = None,
    ) -> Tuple[str, List[RetrievedChunk], float, float, int, int]:
        """Executes full RAG query.

        Returns (answer, retrieved_chunks, retrieval_ms, generation_ms, prompt_tokens, comp_tokens).
        """
        # 1. Retrieval
        t0 = time.perf_counter()
        retrieved = self.retrieve(question)
        retrieved = apply_retrieval_protocol(item, retrieved)
        retrieval_ms = (time.perf_counter() - t0) * 1000.0

        # 2. Generation
        t1 = time.perf_counter()
        answer, prompt_tokens, comp_tokens = self.generator.generate(question, retrieved, item)
        generation_ms = (time.perf_counter() - t1) * 1000.0

        return answer, retrieved, retrieval_ms, generation_ms, prompt_tokens, comp_tokens
