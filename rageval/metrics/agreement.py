"""Inter-annotator agreement. Cohen's kappa and percent agreement on aligned labels."""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

from rageval.core.labels import EVAL_LABEL_ORDER, VerificationLabel, parse_verification_label


def percent_agreement(
    y1: Sequence[VerificationLabel | str],
    y2: Sequence[VerificationLabel | str],
) -> float:
    if not y1:
        return 0.0
    if len(y1) != len(y2):
        raise ValueError("raters must have the same number of labels")
    agree = sum(
        1
        for a, b in zip(y1, y2)
        if parse_verification_label(a) == parse_verification_label(b)
    )
    return round(agree / len(y1), 4)


def cohen_kappa(
    y1: Sequence[VerificationLabel | str],
    y2: Sequence[VerificationLabel | str],
    labels: Sequence[VerificationLabel] = EVAL_LABEL_ORDER,
) -> Optional[float]:
    """Cohen's kappa. None when chance agreement is 1 (undefined)."""
    if not y1:
        return None
    if len(y1) != len(y2):
        raise ValueError("raters must have the same number of labels")
    n = len(y1)
    a = [parse_verification_label(v) for v in y1]
    b = [parse_verification_label(v) for v in y2]
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca = Counter(a)
    cb = Counter(b)
    pe = sum((ca[lab] / n) * (cb[lab] / n) for lab in labels)
    if pe >= 1.0:
        return None
    return round((po - pe) / (1.0 - pe), 4)


def confusion_pairs(
    y1: Sequence[VerificationLabel | str],
    y2: Sequence[VerificationLabel | str],
    labels: Sequence[VerificationLabel] = EVAL_LABEL_ORDER,
) -> List[List[int]]:
    if len(y1) != len(y2):
        raise ValueError("raters must have the same number of labels")
    index = {lab: i for i, lab in enumerate(labels)}
    matrix = [[0 for _ in labels] for _ in labels]
    for left, right in zip(y1, y2):
        i = index[parse_verification_label(left)]
        j = index[parse_verification_label(right)]
        matrix[i][j] += 1
    return matrix


def summarize_agreement(
    ids: Sequence[str],
    y1: Sequence[VerificationLabel | str],
    y2: Sequence[VerificationLabel | str],
) -> Dict[str, object]:
    disagreements: List[Tuple[str, str, str]] = []
    for item_id, left, right in zip(ids, y1, y2):
        a = parse_verification_label(left).value
        b = parse_verification_label(right).value
        if a != b:
            disagreements.append((item_id, a, b))
    return {
        "n": len(ids),
        "percent_agreement": percent_agreement(y1, y2),
        "cohen_kappa": cohen_kappa(y1, y2),
        "n_disagreements": len(disagreements),
        "disagreements": [
            {"id": i, "rater_a": a, "rater_b": b} for i, a, b in disagreements
        ],
    }
