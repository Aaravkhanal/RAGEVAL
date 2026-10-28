"""Unit tests for text chunking algorithms."""

import pytest
from ragtruth.core.schemas import Document
from ragtruth.pipeline.chunkers import FixedTokenChunker, SentenceWindowChunker


def test_fixed_token_chunker():
    doc = Document(
        id="doc_test",
        title="Test Document",
        text="The quick brown fox jumps over the lazy dog. It was a sunny afternoon in the forest.",
    )
    chunker = FixedTokenChunker(chunk_size=6, chunk_overlap=2)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) > 1
    assert chunks[0].doc_id == "doc_test"
    assert chunks[0].chunk_index == 0
    assert chunks[0].token_count <= 6
    assert "quick" in chunks[0].text


def test_sentence_window_chunker():
    doc = Document(
        id="doc_test_2",
        title="Test Sentences",
        text="Sentence one is introductory. Sentence two contains key data. Sentence three concludes the section.",
    )
    chunker = SentenceWindowChunker(window_size=1)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 3
    assert chunks[1].chunk_index == 1
    # Middle sentence chunk should include sentence 1 and sentence 3 in its window
    assert "Sentence one" in chunks[1].text
    assert "Sentence two" in chunks[1].text
    assert "Sentence three" in chunks[1].text
