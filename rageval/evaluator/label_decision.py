"""Map 3-way NLI scores onto the versioned 5-way claim schema.

Dual support+contradiction evidence is never dropped from the verification
record. This module only chooses the *collapsed* label.
"""

from __future__ import annotations

from typing import Tuple

from rageval.core.labels import LABEL_SCHEMA_VERSION, VerificationLabel

ENTAIL_THRESHOLD = 0.50
CONTRA_THRESHOLD = 0.60
PARTIAL_THRESHOLD = 0.30


def decide_claim_label(
    best_entailment: float,
    best_contradiction: float,
    n_supporting: int,
    n_contradicting: int,
    *,
    entail_threshold: float = ENTAIL_THRESHOLD,
    contra_threshold: float = CONTRA_THRESHOLD,
    partial_threshold: float = PARTIAL_THRESHOLD,
) -> Tuple[VerificationLabel, str]:
    """Return (label, explanation) from NLI maxima and dual-evidence counts.

    Collapse rule (rageval.claim_labels.v1):

    1. CONTRADICTED if max contradiction > contra_threshold and strictly
       greater than max entailment.
    2. PARTIALLY_SUPPORTED if both a supporting chunk and a contradicting
       chunk were recorded (dual evidence) or if max entailment is in
       [partial_threshold, entail_threshold).
    3. SUPPORTED if max entailment >= entail_threshold.
    4. UNSUPPORTED otherwise.

    Abstention is handled by the caller (AMBIGUOUS).
    """
    dual = n_supporting > 0 and n_contradicting > 0
    if best_contradiction > contra_threshold and best_contradiction > best_entailment:
        reason = "Claim contradicts retrieved evidence"
        if dual:
            reason += " (supporting chunks retained on the record)"
        return VerificationLabel.CONTRADICTED, reason + "."
    if dual:
        return (
            VerificationLabel.PARTIALLY_SUPPORTED,
            "Dual evidence: at least one chunk supports and one chunk contradicts; "
            "both id lists are retained.",
        )
    if best_entailment >= entail_threshold:
        return VerificationLabel.SUPPORTED, "Claim is entailed by source evidence."
    if best_entailment >= partial_threshold:
        return (
            VerificationLabel.PARTIALLY_SUPPORTED,
            "Claim is only partially entailed (NLI entailment between "
            f"{partial_threshold:.2f} and {entail_threshold:.2f}).",
        )
    return VerificationLabel.UNSUPPORTED, "Claim lacks supporting evidence in the retrieved context."


def schema_version() -> str:
    return LABEL_SCHEMA_VERSION
