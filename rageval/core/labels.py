"""Canonical claim-support labels and loaders for historical aliases."""

from __future__ import annotations

from enum import Enum
from typing import Any


class VerificationLabel(str, Enum):
    """Relationship between a claim and the supplied evidence.

    These labels measure evidence support, not independent world truth.
    """

    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"
    AMBIGUOUS = "ambiguous"

    # Historical aliases from the RAGTruth prototype (same values).
    ENTAILEMENT = "supported"
    CONTRADICTION = "contradicted"
    NEUTRAL = "unsupported"


_ALIASES = {
    "supported": VerificationLabel.SUPPORTED,
    "partially_supported": VerificationLabel.PARTIALLY_SUPPORTED,
    "partial": VerificationLabel.PARTIALLY_SUPPORTED,
    "unsupported": VerificationLabel.UNSUPPORTED,
    "contradicted": VerificationLabel.CONTRADICTED,
    "contradiction": VerificationLabel.CONTRADICTED,
    "ambiguous": VerificationLabel.AMBIGUOUS,
    "unverifiable": VerificationLabel.AMBIGUOUS,
    "entailment": VerificationLabel.SUPPORTED,
    "entailement": VerificationLabel.SUPPORTED,
    "neutral": VerificationLabel.UNSUPPORTED,
}


def parse_verification_label(value: Any) -> VerificationLabel:
    if isinstance(value, VerificationLabel):
        return VerificationLabel(value.value)
    if value is None:
        raise ValueError("Verification label is required")
    key = str(value).strip().lower()
    if key not in _ALIASES:
        raise ValueError(f"Unknown verification label: {value!r}")
    return _ALIASES[key]


FACTUAL_LABELS = (
    VerificationLabel.SUPPORTED,
    VerificationLabel.PARTIALLY_SUPPORTED,
    VerificationLabel.UNSUPPORTED,
    VerificationLabel.CONTRADICTED,
    VerificationLabel.AMBIGUOUS,
)

# Versioned 5-way schema used by ClaimVerification.label_schema_version
LABEL_SCHEMA_VERSION = "rageval.claim_labels.v1"

# Official evaluation classes (abstention maps to AMBIGUOUS and is excluded from rates)
EVAL_LABEL_ORDER = (
    VerificationLabel.SUPPORTED,
    VerificationLabel.PARTIALLY_SUPPORTED,
    VerificationLabel.UNSUPPORTED,
    VerificationLabel.CONTRADICTED,
    VerificationLabel.AMBIGUOUS,
)
