"""Unit tests for multi-hop evidence fusion."""

from rageval.core.schemas import AtomicClaim, Chunk, RetrievedChunk, ClaimVerification, VerificationLabel
from rageval.evaluator.multi_hop import MultiHopEvidenceFusion


def test_multi_hop_chunk_pair_discovery():
    chunk1 = RetrievedChunk(
        chunk=Chunk(
            id="c1", doc_id="d1",
            text="In 2023, ApexCloud generated $680 million in annual enterprise subscription revenue.",
            chunk_index=0, token_count=12, start_char=0, end_char=80,
        ),
        score=0.9, rank=1,
    )
    chunk2 = RetrievedChunk(
        chunk=Chunk(
            id="c2", doc_id="d2",
            text="In 2024, ApexCloud grew total subscription revenue to $842 million with 24% expansion.",
            chunk_index=0, token_count=13, start_char=0, end_char=80,
        ),
        score=0.85, rank=2,
    )

    claim = AtomicClaim(
        claim_id="cm1",
        text="ApexCloud expanded subscription revenue from $680 million in 2023 to $842 million in 2024",
        raw_sentence="ApexCloud expanded subscription revenue from $680 million in 2023 to $842 million in 2024.",
    )

    fusion = MultiHopEvidenceFusion()
    pairs = fusion.find_complementary_chunk_pairs(claim, [chunk1, chunk2])

    assert len(pairs) >= 1
    p1, p2 = pairs[0]
    assert {p1.chunk.id, p2.chunk.id} == {"c1", "c2"}


def test_multi_hop_evaluation_fallback():
    fusion = MultiHopEvidenceFusion()
    claim = AtomicClaim(claim_id="cm2", text="Simple single claim", raw_sentence="Simple single claim.")
    dummy_verif = ClaimVerification(
        claim_id="cm2", claim_text="Simple single claim", label=VerificationLabel.SUPPORTED,
        confidence=1.0, entailment_prob=1.0, neutral_prob=0.0, contradiction_prob=0.0,
    )
    # Already supported claims should pass through immediately
    res = fusion.evaluate_multi_hop_claim(claim, [], dummy_verif)
    assert res.label == VerificationLabel.SUPPORTED
