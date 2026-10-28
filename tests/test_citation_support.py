"""Citation existence vs support-conditioned metrics."""

from rageval.core.labels import VerificationLabel
from rageval.core.schemas import AtomicClaim, Chunk, ClaimVerification, RetrievedChunk
from rageval.evaluator.citation_parser import CitationParser


def _chunks():
    return [
        RetrievedChunk(
            chunk=Chunk(
                id="c1",
                doc_id="d1",
                text="Revenue was 412 million.",
                chunk_index=0,
                token_count=4,
                start_char=0,
                end_char=24,
            ),
            score=1.0,
            rank=1,
        ),
        RetrievedChunk(
            chunk=Chunk(
                id="c2",
                doc_id="d2",
                text="Churn was 1.8 percent.",
                chunk_index=1,
                token_count=4,
                start_char=0,
                end_char=22,
            ),
            score=0.9,
            rank=2,
        ),
    ]


def test_existence_precision_ignores_support():
    chunks = _chunks()
    metric = CitationParser.audit_citations("Revenue was 412 million [1]. Extra [9].", chunks)
    assert metric.total_citations == 2
    assert metric.valid_citations == 1
    assert metric.citation_precision == 0.5


def test_support_precision_and_contradicting_citation():
    chunks = _chunks()
    claims = [
        AtomicClaim(
            claim_id="a",
            text="Revenue was 412 million",
            raw_sentence="Revenue was 412 million [1].",
            cited_chunk_ids=["c1"],
        ),
        AtomicClaim(
            claim_id="b",
            text="Churn was 9.8 percent",
            raw_sentence="Churn was 9.8 percent [2].",
            cited_chunk_ids=["c2"],
        ),
        AtomicClaim(
            claim_id="c",
            text="The firm has 48000 Osaka staff",
            raw_sentence="The firm has 48000 Osaka staff.",
            cited_chunk_ids=[],
        ),
    ]
    verifs = [
        ClaimVerification(
            claim_id="a",
            claim_text=claims[0].text,
            label=VerificationLabel.SUPPORTED,
            supporting_chunk_ids=["c1"],
        ),
        ClaimVerification(
            claim_id="b",
            claim_text=claims[1].text,
            label=VerificationLabel.CONTRADICTED,
            contradiction_prob=0.8,
            contradicting_chunk_ids=["c2"],
        ),
        ClaimVerification(
            claim_id="c",
            claim_text=claims[2].text,
            label=VerificationLabel.UNSUPPORTED,
        ),
    ]
    text = "Revenue was 412 million [1]. Churn was 9.8 percent [2]. The firm has 48000 Osaka staff."
    metric = CitationParser.audit_citations_with_claims(text, chunks, claims, verifs)
    assert metric.citation_support_precision == 0.5
    assert any("b->c2" in x for x in metric.contradicting_citations)
    assert "c" in metric.uncited_claim_ids
    assert metric.citation_completeness == 1.0 / 3.0
