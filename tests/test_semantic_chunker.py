"""Unit tests for semantic sentence-distance chunking."""

import pytest

pytest.importorskip("torch")
pytest.importorskip("sentence_transformers")
pytestmark = pytest.mark.hf

from rageval.core.schemas import Document
from rageval.pipeline.semantic_chunker import SemanticChunker


def test_semantic_chunker():
    doc = Document(
        id="doc_sem_test",
        title="Cross Domain Transition",
        text=(
            "ApexCloud non-GAAP gross margin expanded by 180 basis points to 78.2% in Q3 2024. "
            "Deploying custom ASIC silicon across edge datacenters fueled this financial expansion. "
            "In completely unrelated biomedical oncology research, Veloceptin demonstrated an ORR of 58.4%. "
            "Colitis and immune adverse events occurred in 31% of chemotherapy trial participants."
        ),
    )

    chunker = SemanticChunker(similarity_threshold=0.85, min_chunk_sentences=1, max_chunk_sentences=3)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 2
    assert "ApexCloud" in chunks[0].text
    # Ensure chunk boundary preserved financial sentences together
    assert "gross margin" in chunks[0].text
