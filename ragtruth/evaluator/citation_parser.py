"""Citation parser and reference attribution extractor."""

from __future__ import annotations
import re
from typing import List, Tuple, Set
from ragtruth.core.schemas import RetrievedChunk, CitationMetric


class CitationParser:
    """Parses inline numeric and bracketed document citations (e.g., [1], [2], [1, 3], [doc_fin_01])."""

    CITATION_REGEX = re.compile(r"\[(\d+(?:\s*,\s*\d+)*|[a-zA-Z0-9_\-]+)\]")

    @classmethod
    def extract_citations(cls, text: str) -> List[str]:
        """Returns a list of raw citation strings extracted from text, e.g. ['1', '2', 'doc_fin_01']."""
        raw_matches = cls.CITATION_REGEX.findall(text)
        citations: List[str] = []
        for match in raw_matches:
            if "," in match:
                parts = [p.strip() for p in match.split(",") if p.strip()]
                citations.extend(parts)
            else:
                citations.append(match.strip())
        return citations

    @classmethod
    def strip_citations(cls, text: str) -> str:
        """Removes citation brackets from text for clean linguistic analysis."""
        cleaned = cls.CITATION_REGEX.sub("", text)
        return re.sub(r"\s+", " ", cleaned).strip()

    @classmethod
    def map_citation_to_chunks(
        cls,
        citation_token: str,
        retrieved_chunks: List[RetrievedChunk],
    ) -> List[str]:
        """Resolves a citation token (such as '1' or 'doc_fin_01') to corresponding Chunk IDs."""
        resolved_chunk_ids: List[str] = []

        # 1. 1-indexed numeric citation [1], [2] -> ranks 1, 2
        if citation_token.isdigit():
            idx = int(citation_token) - 1
            if 0 <= idx < len(retrieved_chunks):
                resolved_chunk_ids.append(retrieved_chunks[idx].chunk.id)
            return resolved_chunk_ids

        # 2. Match chunk id or document id directly
        for r in retrieved_chunks:
            if r.chunk.id == citation_token or r.chunk.doc_id == citation_token:
                resolved_chunk_ids.append(r.chunk.id)

        return resolved_chunk_ids

    @classmethod
    def audit_citations(
        cls,
        text: str,
        retrieved_chunks: List[RetrievedChunk],
    ) -> CitationMetric:
        """Audits citations in the text to identify valid vs hallucinated (out-of-bounds) citations."""
        citations = cls.extract_citations(text)
        total_citations = len(citations)
        
        valid_count = 0
        hallucinated_citations: List[str] = []

        num_retrieved = len(retrieved_chunks)

        for c in citations:
            if c.isdigit():
                val = int(c)
                if 1 <= val <= num_retrieved:
                    valid_count += 1
                else:
                    hallucinated_citations.append(f"[{c}] (retrieved pool only has {num_retrieved} chunks)")
            else:
                matches = cls.map_citation_to_chunks(c, retrieved_chunks)
                if matches:
                    valid_count += 1
                else:
                    hallucinated_citations.append(f"[{c}] (not found in retrieved chunks)")

        precision = (valid_count / total_citations) if total_citations > 0 else 1.0
        # Citation recall measures whether sentences contain citations
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        sentences_with_citation = sum(1 for s in sentences if cls.extract_citations(s))
        recall = (sentences_with_citation / len(sentences)) if sentences else 1.0

        return CitationMetric(
            total_citations=total_citations,
            valid_citations=valid_count,
            hallucinated_citations=hallucinated_citations,
            citation_precision=precision,
            citation_recall=recall,
        )
