"""Atomic Claim Decomposition Engine: Splits complex responses into verifiable propositions."""

from __future__ import annotations
import re
from typing import List
from rageval.core.schemas import AtomicClaim, RetrievedChunk
from rageval.evaluator.citation_parser import CitationParser


class AtomicClaimDecomposer:
    """Decomposes generated answers into individual atomic factual claims

    while preserving cited source markers and clause boundaries.
    """

    DISCOURSE_MARKERS = [
        r"^in summary,?\s*",
        r"^overall,?\s*",
        r"^according to the (provided )?(context|documents|sources|text),?\s*",
        r"^as stated (in the documents|above),?\s*",
        r"^furthermore,?\s*",
        r"^moreover,?\s*",
        r"^in addition,?\s*",
        r"^based on the (given )?(context|information),?\s*",
    ]

    CONJUNCTION_SPLITTERS = [
        r",\s*and\s+(?=[A-Z0-9a-z])",
        r";\s*",
        r",\s*while\s+",
        r",\s*whereas\s+",
    ]

    @classmethod
    def clean_discourse(cls, text: str) -> str:
        cleaned = text.strip()
        for marker in cls.DISCOURSE_MARKERS:
            cleaned = re.sub(marker, "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned

    @classmethod
    def decompose(cls, answer: str, retrieved_chunks: List[RetrievedChunk] = None) -> List[AtomicClaim]:
        if not answer or not answer.strip():
            return []

        retrieved_chunks = retrieved_chunks or []
        sentence_spans = cls._sentence_spans(answer)

        atomic_claims: List[AtomicClaim] = []
        claim_counter = 1

        for raw_sent, sent_start, sent_end in sentence_spans:
            cleaned_sent = cls.clean_discourse(raw_sent)
            if not cleaned_sent:
                continue

            # Check if this sentence is an explicit abstention
            lower_sent = cleaned_sent.lower()

            if any(term in lower_sent for term in ["do not have sufficient information", "cannot be answered", "insufficient context", "not enough information"]):
                atomic_claims.append(
                    AtomicClaim(
                        claim_id=f"claim_{claim_counter}",
                        text=cleaned_sent,
                        raw_sentence=raw_sent,
                        cited_chunk_ids=[],
                        char_start=sent_start,
                        char_end=sent_end,
                        is_abstention=True,
                    )
                )
                claim_counter += 1
                continue

            # Extract citations from the sentence
            raw_citations = CitationParser.extract_citations(raw_sent)
            resolved_chunk_ids: List[str] = []
            for c in raw_citations:
                resolved_chunk_ids.extend(CitationParser.map_citation_to_chunks(c, retrieved_chunks))

            # Check for multi-clause conjunctions to produce finer atomic propositions
            sub_clauses = [cleaned_sent]
            for pattern in cls.CONJUNCTION_SPLITTERS:
                new_clauses = []
                for clause in sub_clauses:
                    parts = re.split(pattern, clause)
                    new_clauses.extend([p.strip() for p in parts if len(p.strip().split()) >= 3])
                if new_clauses:
                    sub_clauses = new_clauses

            for clause in sub_clauses:
                # Strip citation brackets from the claim text itself
                claim_text = CitationParser.strip_citations(clause).strip()
                if not claim_text or len(claim_text.split()) < 2:
                    continue

                clause_start, clause_end = cls._span_in_answer(
                    answer, sent_start, sent_end, raw_sent, clause, claim_text
                )

                atomic_claims.append(
                    AtomicClaim(
                        claim_id=f"claim_{claim_counter}",
                        text=claim_text,
                        raw_sentence=raw_sent,
                        cited_chunk_ids=list(dict.fromkeys(resolved_chunk_ids)),
                        char_start=clause_start,
                        char_end=clause_end,
                        is_abstention=False,
                    )
                )
                claim_counter += 1

        return atomic_claims

    @classmethod
    def _sentence_spans(cls, answer: str) -> List[tuple[str, int, int]]:
        """Split on sentence boundaries and return (text, start, end) into `answer`."""
        parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]
        cursor = 0
        spans: List[tuple[str, int, int]] = []
        for part in parts:
            idx = answer.find(part, cursor)
            if idx < 0:
                idx = answer.find(part)
            if idx < 0:
                continue
            spans.append((part, idx, idx + len(part)))
            cursor = idx + len(part)
        return spans

    @classmethod
    def _span_in_answer(
        cls,
        answer: str,
        sent_start: int,
        sent_end: int,
        raw_sent: str,
        clause: str,
        claim_text: str,
    ) -> tuple[int, int]:
        """Offsets such that answer[start:end] is a substring of the source sentence."""
        for needle in (clause, claim_text):
            if not needle:
                continue
            rel = raw_sent.find(needle)
            if rel >= 0:
                start = sent_start + rel
                end = start + len(needle)
                if answer[start:end] == needle:
                    return start, end
        return sent_start, sent_end
