"""Unit tests for citation extraction and precision/recall auditing."""

from ragtruth.core.schemas import Chunk, RetrievedChunk
from ragtruth.evaluator.citation_parser import CitationParser


def test_citation_extraction():
    text = "ApexCloud grew revenue by 24% [1] and expanded gross margin [2, 3]. Secondary notes [doc_fin_02]."
    citations = CitationParser.extract_citations(text)
    assert citations == ["1", "2", "3", "doc_fin_02"]

    cleaned = CitationParser.strip_citations(text)
    assert "[1]" not in cleaned
    assert "[2, 3]" not in cleaned
    assert "ApexCloud grew revenue by 24% and expanded gross margin" in cleaned


def test_citation_audit_with_hallucinations():
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

    # Valid citation [1] + Hallucinated out-of-pool citation [5]
    text = "Valid factual point [1]. Fabricated attribution claiming support from [5]."
    audit = CitationParser.audit_citations(text, chunks)

    assert audit.total_citations == 2
    assert audit.valid_citations == 1
    assert len(audit.hallucinated_citations) == 1
    assert audit.citation_precision == 0.5
