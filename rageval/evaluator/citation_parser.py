"""Citation parser and reference attribution extractor."""

from __future__ import annotations
import re
from typing import List
from rageval.core.schemas import AtomicClaim, ClaimVerification, RetrievedChunk, CitationMetric
from rageval.core.labels import VerificationLabel
from rageval.metrics.citation import (
    citation_completeness,
    citation_existence_precision,
    citation_marker_recall,
    citation_support_precision,
)


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

        precision = citation_existence_precision(valid_count, total_citations)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        sentences_with_citation = sum(1 for s in sentences if cls.extract_citations(s))
        recall = citation_marker_recall(sentences_with_citation, len(sentences))

        return CitationMetric(
            total_citations=total_citations,
            valid_citations=valid_count,
            hallucinated_citations=hallucinated_citations,
            citation_precision=precision,
            citation_recall=recall,
            citation_support_precision=1.0 if total_citations == 0 else 0.0,
            citation_completeness=1.0,
        )

    @classmethod
    def audit_citations_with_claims(
        cls,
        text: str,
        retrieved_chunks: List[RetrievedChunk],
        claims: List[AtomicClaim],
        verifications: List[ClaimVerification],
    ) -> CitationMetric:
        """Existence audit plus support-conditioned citation metrics."""
        base = cls.audit_citations(text, retrieved_chunks)
        verif_by_id = {v.claim_id: v for v in verifications}

        evaluated = 0
        supporting_cites = 0
        misattributed: List[str] = list(base.misattributed_citations)
        requiring = 0
        with_supporting = 0

        uncited: List[str] = []
        contradicting_cites: List[str] = []

        for claim in claims:
            if claim.is_abstention:
                continue
            verif = verif_by_id.get(claim.claim_id)
            requiring += 1
            if not claim.cited_chunk_ids:
                uncited.append(claim.claim_id)
                continue
            claim_has_support_cite = False
            for cid in claim.cited_chunk_ids:
                evaluated += 1
                supports = bool(verif and cid in verif.supporting_chunk_ids)
                contradicts = bool(verif and cid in verif.contradicting_chunk_ids)
                if supports:
                    supporting_cites += 1
                    claim_has_support_cite = True
                if contradicts:
                    contradicting_cites.append(f"{claim.claim_id}->{cid}")
                if contradicts or (verif and verif.label == VerificationLabel.UNSUPPORTED and not supports):
                    misattributed.append(f"{claim.claim_id}->{cid}")
            if claim_has_support_cite:
                with_supporting += 1

        base.misattributed_citations = misattributed
        base.uncited_claim_ids = uncited
        base.contradicting_citations = contradicting_cites
        base.citation_support_precision = citation_support_precision(supporting_cites, evaluated)
        base.citation_completeness = citation_completeness(with_supporting, requiring)
        return base
