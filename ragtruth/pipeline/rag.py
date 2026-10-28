"""End-to-end RAG pipeline assembling chunking, vector indexing, hybrid search, reranking, and generation."""

from __future__ import annotations
import time
from typing import List, Optional, Tuple
from ragtruth.core.schemas import Document, Chunk, RetrievedChunk, BenchmarkItem
from ragtruth.core.config import PipelineConfig
from ragtruth.pipeline.chunkers import get_chunker
from ragtruth.pipeline.embedders import SentenceTransformerEmbedder
from ragtruth.pipeline.indices import FAISSIndex
from ragtruth.pipeline.sparse import BM25Retriever, HybridRetriever
from ragtruth.pipeline.rerankers import CrossEncoderReranker
from ragtruth.pipeline.generator import get_generator, BaseGenerator


class RAGPipeline:
    """Configurable, modular RAG pipeline under test."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.chunker = get_chunker(self.config.chunker)
        self.embedder = SentenceTransformerEmbedder(self.config.embedder)
        self.faiss_index = FAISSIndex(
            embedder=self.embedder,
            index_type=self.config.retriever.index_type,
        )
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.hybrid_retriever: Optional[HybridRetriever] = None
        self.reranker = CrossEncoderReranker(self.config.reranker)
        self.generator: BaseGenerator = get_generator(self.config.generator)
        self.documents: List[Document] = []
        self.chunks: List[Chunk] = []

    def index(self, documents: List[Document]) -> None:
        """Chunks documents and builds dense and sparse indices."""
        self.documents = documents
        self.chunks = self.chunker.chunk_documents(documents)
        
        # Build dense FAISS index
        self.faiss_index.build(self.chunks)

        # Build sparse BM25 and hybrid retriever
        self.bm25_retriever = BM25Retriever(self.chunks)
        self.hybrid_retriever = HybridRetriever(
            faiss_index=self.faiss_index,
            bm25_retriever=self.bm25_retriever,
            rrf_k=self.config.retriever.rrf_k,
        )

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[RetrievedChunk]:
        k = top_k or self.config.retriever.top_k
        method = self.config.retriever.method

        if method == "sparse" and self.bm25_retriever:
            candidates = self.bm25_retriever.search(query, top_k=k)
        elif method == "hybrid" and self.hybrid_retriever:
            candidates = self.hybrid_retriever.search(query, top_k=k)
        else:
            candidates = self.faiss_index.search(query, top_k=k)

        # Apply reranking if configured
        if self.config.reranker.enabled:
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
        retrieval_ms = (time.perf_counter() - t0) * 1000.0

        # 2. Generation
        t1 = time.perf_counter()
        answer, prompt_tokens, comp_tokens = self.generator.generate(question, retrieved, item)
        generation_ms = (time.perf_counter() - t1) * 1000.0

        return answer, retrieved, retrieval_ms, generation_ms, prompt_tokens, comp_tokens
