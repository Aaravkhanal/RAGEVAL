"""Span-level evidence localization for pinpointing verbatim source spans."""

from __future__ import annotations
import re
from typing import List, Tuple, Optional, Dict
from pydantic import BaseModel
from ragtruth.core.schemas import AtomicClaim, Chunk


class EvidenceSpanMatch(BaseModel):
    chunk_id: str
    doc_id: str
    start_char: int
    end_char: int
    exact_span: str
    overlap_score: float
    is_supporting: bool


class SpanLocalizer:
    """Pinpoints the exact character boundaries within a context chunk

    that provides direct evidence (or contradiction) for an atomic claim.
    """

    @classmethod
    def split_sentences_with_offsets(cls, text: str) -> List[Tuple[str, int, int]]:
        """Returns list of (sentence_text, start_char, end_char), preserving decimal numbers."""
        pattern = re.compile(r'.*?(?:(?<=[.!?])(?<!\d\.)(?=\s+[A-Z0-9]|$))', re.DOTALL)
        spans = []
        for m in pattern.finditer(text):
            raw = m.group()
            s_text = raw.strip()
            if s_text:
                lead_space = len(raw) - len(raw.lstrip())
                start = m.start() + lead_space
                end = start + len(s_text)
                spans.append((s_text, start, end))
        return spans

    @classmethod
    def find_best_evidence_span(
        cls,
        claim_text: str,
        chunk: Chunk,
        is_supporting: bool = True,
    ) -> Optional[EvidenceSpanMatch]:
        """Finds the sentence in `chunk` that shares the highest semantic/lexical overlap with `claim_text`."""
        sentences = cls.split_sentences_with_offsets(chunk.text)
        if not sentences:
            return None

        claim_tokens = set(re.findall(r"\w+", claim_text.lower()))
        if not claim_tokens:
            return None

        # Filter common stopwords for more precise matching
        stopwords = {"the", "a", "an", "is", "was", "are", "were", "in", "on", "at", "to", "for", "of", "and", "or"}
        claim_content_words = claim_tokens - stopwords
        if not claim_content_words:
            claim_content_words = claim_tokens

        best_score = 0.0
        best_span: Optional[Tuple[str, int, int]] = None

        for sent_text, start, end in sentences:
            sent_tokens = set(re.findall(r"\w+", sent_text.lower()))
            intersection = claim_content_words & sent_tokens
            # Jaccard-like content overlap
            score = len(intersection) / max(len(claim_content_words), 1)

            # Bonus for matching numbers / percentages
            claim_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", claim_text))
            sent_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", sent_text))
            if claim_nums and sent_nums and (claim_nums & sent_nums):
                score += 0.35

            if score > best_score:
                best_score = score
                best_span = (sent_text, start, end)

        if best_span and best_score >= 0.25:
            return EvidenceSpanMatch(
                chunk_id=chunk.id,
                doc_id=chunk.doc_id,
                start_char=best_span[1],
                end_char=best_span[2],
                exact_span=best_span[0],
                overlap_score=round(best_score, 4),
                is_supporting=is_supporting,
            )

        return None
