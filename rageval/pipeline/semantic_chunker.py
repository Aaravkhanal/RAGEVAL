"""Semantic chunking using sentence embedding cosine similarity distance."""

from __future__ import annotations
import re
from typing import List, Optional
import numpy as np
from rageval.core.schemas import Document, Chunk
from rageval.pipeline.chunkers import BaseChunker
from rageval.pipeline.embedders import SentenceTransformerEmbedder


class SemanticChunker(BaseChunker):
    """Splits text by monitoring cosine distance between consecutive sentence embeddings.

    When the semantic transition between sentence (i) and (i+1) drops below the similarity threshold,
    a chunk boundary is created, ensuring high internal thematic coherence.
    """

    def __init__(
        self,
        embedder: Optional[SentenceTransformerEmbedder] = None,
        similarity_threshold: float = 0.65,
        min_chunk_sentences: int = 1,
        max_chunk_sentences: int = 6,
    ):
        self.embedder = embedder or SentenceTransformerEmbedder()
        self.similarity_threshold = similarity_threshold
        self.min_chunk_sentences = min_chunk_sentences
        self.max_chunk_sentences = max_chunk_sentences

    def _split_into_sentences(self, text: str) -> List[str]:
        raw_sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in raw_sentences if len(s.strip().split()) >= 2]

    def chunk_document(self, document: Document) -> List[Chunk]:
        sentences = self._split_into_sentences(document.text)
        if not sentences:
            return []

        if len(sentences) == 1:
            return [
                Chunk(
                    id=f"{document.id}_sem_0",
                    doc_id=document.id,
                    text=sentences[0],
                    chunk_index=0,
                    token_count=len(sentences[0].split()),
                    start_char=0,
                    end_char=len(sentences[0]),
                    metadata={"title": document.title, "domain": document.domain},
                )
            ]

        # Compute embeddings for all sentences
        embeddings = self.embedder.encode(sentences)

        # Compute cosine similarity between adjacent sentence pairs
        # Since embeddings from SentenceTransformerEmbedder are L2 normalized, inner product = cosine similarity
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = float(np.dot(embeddings[i], embeddings[i + 1]))
            similarities.append(sim)

        chunks: List[Chunk] = []
        current_chunk_sentences: List[str] = [sentences[0]]
        chunk_idx = 0

        for i, sim in enumerate(similarities):
            next_sent = sentences[i + 1]
            num_current = len(current_chunk_sentences)

            # Split condition: similarity is below threshold AND min sentences met, OR max sentences reached
            should_split = (
                (sim < self.similarity_threshold and num_current >= self.min_chunk_sentences)
                or (num_current >= self.max_chunk_sentences)
            )

            if should_split:
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append(
                    Chunk(
                        id=f"{document.id}_sem_{chunk_idx}",
                        doc_id=document.id,
                        text=chunk_text,
                        chunk_index=chunk_idx,
                        token_count=len(chunk_text.split()),
                        start_char=0,
                        end_char=len(chunk_text),
                        metadata={"title": document.title, "domain": document.domain, "sentence_count": num_current},
                    )
                )
                chunk_idx += 1
                current_chunk_sentences = [next_sent]
            else:
                current_chunk_sentences.append(next_sent)

        # Append final remaining chunk
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append(
                Chunk(
                    id=f"{document.id}_sem_{chunk_idx}",
                    doc_id=document.id,
                    text=chunk_text,
                    chunk_index=chunk_idx,
                    token_count=len(chunk_text.split()),
                    start_char=0,
                    end_char=len(chunk_text),
                    metadata={"title": document.title, "domain": document.domain, "sentence_count": len(current_chunk_sentences)},
                )
            )

        return chunks
