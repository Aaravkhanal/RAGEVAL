"""Unit tests for atomic claim decomposition."""

from ragtruth.core.schemas import Chunk, RetrievedChunk
from ragtruth.evaluator.decomposer import AtomicClaimDecomposer


def test_atomic_claim_decomposition():
    answer = (
        "In summary, ApexCloud achieved a gross margin of 78.2% [1], "
        "and this expansion was driven by custom ASIC silicon deployment [1]. "
        "Moreover, operating cash flow reached $215 million [2]."
    )
    chunks = [
        RetrievedChunk(
            chunk=Chunk(id="c1", doc_id="d1", text="Chunk 1", chunk_index=0, token_count=2, start_char=0, end_char=7),
            score=0.9, rank=1,
        ),
        RetrievedChunk(
            chunk=Chunk(id="c2", doc_id="d2", text="Chunk 2", chunk_index=1, token_count=2, start_char=0, end_char=7),
            score=0.8, rank=2,
        ),
    ]

    claims = AtomicClaimDecomposer.decompose(answer, chunks)
    assert len(claims) >= 2

    # Verify discourse markers ("In summary", "Moreover") are cleaned
    for c in claims:
        assert not c.text.lower().startswith("in summary")
        assert not c.text.lower().startswith("moreover")
        assert "[" not in c.text  # Brackets stripped from claim proposition

    # Verify citation preservation
    assert "c1" in claims[0].cited_chunk_ids
