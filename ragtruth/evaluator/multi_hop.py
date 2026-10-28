"""Multi-hop evidence fusion: synthesizes cross-document premises for complex propositions."""

from __future__ import annotations
import re
from typing import List, Tuple, Optional, Set
from ragtruth.core.schemas import AtomicClaim, RetrievedChunk, ClaimVerification, VerificationLabel
from ragtruth.evaluator.nli_verifier import NLIVerifier


class MultiHopEvidenceFusion:
    """Detects when an atomic proposition requires synthesizing facts across multiple candidate chunks

    (e.g., temporal comparisons, multi-entity associations) and evaluates fused composite premises.
    """

    def __init__(self, nli_verifier: Optional[NLIVerifier] = None):
        self.verifier = nli_verifier or NLIVerifier()

    @staticmethod
    def _extract_content_entities(text: str) -> Set[str]:
        words = set(re.findall(r"\b[A-Za-z0-9\$\%]{3,}\b", text.lower()))
        stopwords = {
            "the", "and", "was", "were", "with", "from", "that", "this", "have", "been",
            "they", "what", "which", "will", "would", "could", "should", "than", "then",
        }
        return words - stopwords

    def find_complementary_chunk_pairs(
        self,
        claim: AtomicClaim,
        candidate_chunks: List[RetrievedChunk],
        max_pairs: int = 4,
    ) -> List[Tuple[RetrievedChunk, RetrievedChunk]]:
        """Identifies pairs of chunks that individually share partial overlap with the claim."""
        claim_entities = self._extract_content_entities(claim.text)
        if len(claim_entities) < 2 or len(candidate_chunks) < 2:
            return []

        # Score chunks by partial overlap
        chunk_overlaps = []
        for c in candidate_chunks:
            c_entities = self._extract_content_entities(c.chunk.text)
            overlap = len(claim_entities & c_entities)
            if overlap >= 1:
                chunk_overlaps.append((c, c_entities, overlap))

        chunk_overlaps.sort(key=lambda x: x[2], reverse=True)

        candidate_pairs: List[Tuple[RetrievedChunk, RetrievedChunk]] = []
        for i in range(len(chunk_overlaps)):
            for j in range(i + 1, len(chunk_overlaps)):
                c1, e1, _ = chunk_overlaps[i]
                c2, e2, _ = chunk_overlaps[j]

                # If union of both chunks covers more of the claim's entities than either chunk alone
                union_coverage = len(claim_entities & (e1 | e2))
                if union_coverage > len(claim_entities & e1) and union_coverage > len(claim_entities & e2):
                    candidate_pairs.append((c1, c2))
                    if len(candidate_pairs) >= max_pairs:
                        return candidate_pairs

        return candidate_pairs

    def evaluate_multi_hop_claim(
        self,
        claim: AtomicClaim,
        retrieved_chunks: List[RetrievedChunk],
        single_chunk_verif: ClaimVerification,
    ) -> ClaimVerification:
        """If single chunk verification yielded NEUTRAL (unsupported), attempts multi-hop premise fusion."""
        # Only attempt multi-hop if single-chunk verification was inconclusive (NEUTRAL)
        if single_chunk_verif.label == VerificationLabel.ENTAILEMENT:
            return single_chunk_verif

        pairs = self.find_complementary_chunk_pairs(claim, retrieved_chunks)
        if not pairs:
            return single_chunk_verif

        for c1, c2 in pairs:
            composite_premise = f"{c1.chunk.text} Furthermore, {c2.chunk.text}"
            nli_res = self.verifier._predict_nli_batch([(composite_premise, claim.text)])
            if not nli_res:
                continue

            scores = nli_res[0]
            if scores["entailment"] >= 0.50 and scores["entailment"] > scores["contradiction"]:
                return ClaimVerification(
                    claim_id=claim.claim_id,
                    claim_text=claim.text,
                    label=VerificationLabel.ENTAILEMENT,
                    confidence=round(scores["entailment"], 4),
                    entailment_prob=round(scores["entailment"], 4),
                    neutral_prob=round(scores["neutral"], 4),
                    contradiction_prob=round(scores["contradiction"], 4),
                    supporting_chunk_ids=[c1.chunk.id, c2.chunk.id],
                    best_matching_chunk_id=f"{c1.chunk.id}+{c2.chunk.id}",
                    best_matching_chunk_text=composite_premise,
                    evidence_exact_text=f"{c1.chunk.text[:60]}... + {c2.chunk.text[:60]}...",
                    explanation="Claim is verified via multi-hop evidence fusion across complementary source chunks.",
                )

        return single_chunk_verif
