"""Unit tests for FAISS dense indexing and BM25 hybrid search."""

from ragtruth.core.schemas import Document, Chunk
from ragtruth.pipeline.chunkers import FixedTokenChunker
from ragtruth.pipeline.embedders import SentenceTransformerEmbedder
from ragtruth.pipeline.indices import FAISSIndex
from ragtruth.pipeline.sparse import BM25Retriever, HybridRetriever


def test_faiss_and_hybrid_retrieval():
    doc1 = Document(
        id="d1",
        title="Doc 1",
        text="HydraKV read latency is 1.4 ms with monotonic read leases in planetary distributed storage.",
    )
    doc2 = Document(
        id="d2",
        title="Doc 2",
        text="Veloceptin achieved 14.8 months median progression free survival in clinical oncology trials.",
    )

    chunker = FixedTokenChunker(chunk_size=100)
    chunks = chunker.chunk_documents([doc1, doc2])

    embedder = SentenceTransformerEmbedder()
    faiss_index = FAISSIndex(embedder)
    faiss_index.build(chunks)

    # Dense search
    dense_res = faiss_index.search("What is HydraKV read latency?", top_k=1)
    assert len(dense_res) == 1
    assert "HydraKV" in dense_res[0].chunk.text

    # BM25 search
    bm25 = BM25Retriever(chunks)
    sparse_res = bm25.search("Veloceptin survival", top_k=1)
    assert len(sparse_res) == 1
    assert "Veloceptin" in sparse_res[0].chunk.text

    # Hybrid RRF search
    hybrid = HybridRetriever(faiss_index, bm25)
    hybrid_res = hybrid.search("HydraKV monotonic read", top_k=2)
    assert len(hybrid_res) >= 1
    assert "HydraKV" in hybrid_res[0].chunk.text
