"""Validation utilities for checking benchmark dataset integrity and coverage."""

from __future__ import annotations
from typing import List, Dict, Any
from rageval.core.schemas import Document, BenchmarkItem, TestType


def validate_benchmark_integrity(
    documents: List[Document],
    items: List[BenchmarkItem]
) -> Dict[str, Any]:
    """Validates that:

    1. All referenced document IDs exist in the corpus.
    2. Gold evidence spans are non-empty and present in the source documents.
    3. Adversarial items have appropriate flags (expected_abstention for unanswerables).
    4. Atomic claims are provided for non-abstention standard benchmark items.
    """
    doc_ids = {doc.id: doc for doc in documents}
    errors = []
    warnings = []

    for item in items:
        # Check doc references in evidence spans
        for ev in item.gold_evidence_spans:
            if ev.doc_id not in doc_ids:
                errors.append(f"Item {item.id} references missing doc_id: {ev.doc_id}")
            else:
                doc_text = doc_ids[ev.doc_id].text
                # Fuzzy or substring check for span
                clean_span = ev.span.split("...")[0].strip()
                if clean_span and clean_span[:30] not in doc_text:
                    warnings.append(f"Item {item.id} gold span prefix not verbatim in {ev.doc_id}")

        # Unanswerable validation
        if item.test_type == TestType.UNANSWERABLE and not item.expected_abstention:
            errors.append(f"Unanswerable item {item.id} must set expected_abstention=True")

        # Standard items should have gold claims
        if item.test_type == TestType.STANDARD and not item.gold_atomic_claims:
            warnings.append(f"Standard item {item.id} has no gold_atomic_claims listed")

    return {
        "valid": len(errors) == 0,
        "total_documents": len(documents),
        "total_benchmark_items": len(items),
        "errors": errors,
        "warnings": warnings,
    }
