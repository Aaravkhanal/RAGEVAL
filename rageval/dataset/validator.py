"""Validation utilities for checking benchmark dataset integrity and coverage."""

from __future__ import annotations

from typing import Any, Dict, List

from rageval.core.labels import VerificationLabel
from rageval.core.schemas import BenchmarkItem, Document, TestType


def validate_benchmark_integrity(
    documents: List[Document],
    items: List[BenchmarkItem],
    *,
    require_license: bool = False,
    require_verbatim_spans: bool = False,
) -> Dict[str, Any]:
    """Validates that:

    1. All referenced document IDs exist in the corpus.
    2. Gold evidence spans are non-empty and present in the source documents.
    3. Adversarial items have appropriate flags (expected_abstention for unanswerables).
    4. Atomic claims are provided for non-abstention standard benchmark items.
    5. Optionally, every document has license + provenance, and spans are verbatim.
    """
    doc_ids = {doc.id: doc for doc in documents}
    errors = []
    warnings = []

    if require_license:
        for doc in documents:
            if not doc.license:
                errors.append(f"Document {doc.id} is missing license")
            if not (doc.provenance or doc.source_url):
                errors.append(f"Document {doc.id} is missing provenance/source_url")

    for item in items:
        for ev in item.gold_evidence_spans:
            if ev.doc_id not in doc_ids:
                errors.append(f"Item {item.id} references missing doc_id: {ev.doc_id}")
            else:
                doc_text = doc_ids[ev.doc_id].text
                if ev.span and ev.span in doc_text:
                    continue
                clean_span = ev.span.split("...")[0].strip()
                if require_verbatim_spans:
                    errors.append(
                        f"Item {item.id} gold span is not a verbatim substring of {ev.doc_id}"
                    )
                elif clean_span and clean_span[:30] not in doc_text:
                    warnings.append(
                        f"Item {item.id} gold span prefix not verbatim in {ev.doc_id}"
                    )

        if item.test_type == TestType.UNANSWERABLE and not item.expected_abstention:
            errors.append(f"Unanswerable item {item.id} must set expected_abstention=True")

        if item.test_type == TestType.STANDARD and not item.gold_atomic_claims:
            warnings.append(f"Standard item {item.id} has no gold_atomic_claims listed")

        if item.scenario_type == "mixed_support":
            statuses = {c.status for c in item.gold_atomic_claims}
            if VerificationLabel.SUPPORTED not in statuses:
                errors.append(f"Mixed-support item {item.id} has no supported gold claim")
            non_supported = statuses - {VerificationLabel.SUPPORTED}
            if not non_supported:
                errors.append(
                    f"Mixed-support item {item.id} has only supported gold claims"
                )

    return {
        "valid": len(errors) == 0,
        "total_documents": len(documents),
        "total_benchmark_items": len(items),
        "errors": errors,
        "warnings": warnings,
    }
