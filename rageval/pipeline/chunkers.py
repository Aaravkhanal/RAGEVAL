"""Text chunking strategies: Fixed-size, Recursive, and Sentence-Window."""

from __future__ import annotations
import re
from abc import ABC, abstractmethod
from typing import List
from rageval.core.schemas import Document, Chunk
from rageval.core.config import ChunkerConfig


class BaseChunker(ABC):
    @abstractmethod
    def chunk_document(self, document: Document) -> List[Chunk]:
        pass

    def chunk_documents(self, documents: List[Document]) -> List[Chunk]:
        all_chunks: List[Chunk] = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks


class FixedTokenChunker(BaseChunker):
    """Splits document text into fixed-size word/token chunks with configurable overlap."""

    def __init__(self, chunk_size: int = 256, chunk_overlap: int = 32):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: Document) -> List[Chunk]:
        words = document.text.split()
        if not words:
            return []

        chunks: List[Chunk] = []
        stride = max(1, self.chunk_size - self.chunk_overlap)
        chunk_idx = 0

        for i in range(0, len(words), stride):
            chunk_words = words[i : i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            # Approximate character boundaries in the original document
            start_char = document.text.find(chunk_text[:30]) if len(chunk_text) >= 30 else 0
            if start_char == -1:
                start_char = 0
            end_char = start_char + len(chunk_text)

            chunk = Chunk(
                id=f"{document.id}_chk_{chunk_idx}",
                doc_id=document.id,
                text=chunk_text,
                chunk_index=chunk_idx,
                token_count=len(chunk_words),
                start_char=start_char,
                end_char=end_char,
                metadata={"title": document.title, "domain": document.domain},
            )
            chunks.append(chunk)
            chunk_idx += 1

            if i + self.chunk_size >= len(words):
                break

        return chunks


class SentenceWindowChunker(BaseChunker):
    """Splits into sentences and attaches a symmetric context window around each sentence."""

    def __init__(self, window_size: int = 2):
        self.window_size = window_size

    def _split_into_sentences(self, text: str) -> List[str]:
        # Regex split on sentence terminators while preserving words
        raw_sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in raw_sentences if s.strip()]

    def chunk_document(self, document: Document) -> List[Chunk]:
        sentences = self._split_into_sentences(document.text)
        if not sentences:
            return []

        chunks: List[Chunk] = []
        for idx, focal_sent in enumerate(sentences):
            start_idx = max(0, idx - self.window_size)
            end_idx = min(len(sentences), idx + self.window_size + 1)
            window_sentences = sentences[start_idx:end_idx]
            window_text = " ".join(window_sentences)

            chunk = Chunk(
                id=f"{document.id}_win_{idx}",
                doc_id=document.id,
                text=window_text,
                chunk_index=idx,
                token_count=len(window_text.split()),
                start_char=0,
                end_char=len(window_text),
                metadata={
                    "title": document.title,
                    "domain": document.domain,
                    "focal_sentence": focal_sent,
                },
            )
            chunks.append(chunk)

        return chunks


def get_chunker(config: ChunkerConfig, embedder=None) -> BaseChunker:
    if config.strategy == "sentence_window":
        return SentenceWindowChunker(window_size=config.window_size)
    elif config.strategy == "semantic":
        from rageval.pipeline.semantic_chunker import SemanticChunker
        return SemanticChunker(embedder=embedder)
    return FixedTokenChunker(chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap)
