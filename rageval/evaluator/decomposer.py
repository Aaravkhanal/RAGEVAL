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
        # Split on sentence boundaries
        raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]

        atomic_claims: List[AtomicClaim] = []
        claim_counter = 1

        for raw_sent in raw_sentences:
            cleaned_sent = cls.clean_discourse(raw_sent)
            if not cleaned_sent:
                continue

            # Check if this sentence is an explicit abstention
            lower_sent = cleaned_sent.lower()
            sent_start = answer.find(raw_sent)
            sent_end = sent_start + len(raw_sent) if sent_start >= 0 else None
            if sent_start < 0:
                sent_start = None

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

                clause_start = None
                clause_end = None
                if sent_start is not None:
                    rel = raw_sent.find(clause[: min(24, len(clause))])
                    clause_start = sent_start + rel if rel >= 0 else sent_start
                    clause_end = clause_start + len(claim_text) if clause_start is not None else sent_end

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
