"""Answer-level exact match and token F1 (SQuAD-style).

These scores compare a generated answer string to a gold answer string.
They do not measure claim-level support against retrieved evidence (RQ3).
"""

from __future__ import annotations

import re
import string
from collections import Counter
from typing import Optional, Sequence, Tuple

from rageval.core.labels import VerificationLabel


_ARTICLES = re.compile(r"\b(a|an|the)\b", re.IGNORECASE)


def normalize_answer(text: str) -> str:
    """Lowercase, strip punctuation and English articles, collapse whitespace."""
    value = (text or "").lower()
    value = value.translate(str.maketrans("", "", string.punctuation))
    value = _ARTICLES.sub(" ", value)
    return " ".join(value.split())


def exact_match(prediction: str, gold: str) -> float:
    """1.0 if normalized strings are identical, else 0.0."""
    return 1.0 if normalize_answer(prediction) == normalize_answer(gold) else 0.0


def token_f1(prediction: str, gold: str) -> float:
    """Bag-of-tokens F1 after normalize_answer. Empty/empty is 1.0."""
    pred_tokens = normalize_answer(prediction).split()
    gold_tokens = normalize_answer(gold).split()
    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0
    overlap = sum((Counter(pred_tokens) & Counter(gold_tokens)).values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(pred_tokens)
    recall = overlap / len(gold_tokens)
    return 2.0 * precision * recall / (precision + recall)


def answer_em_f1(
    prediction: str,
    gold_answer: Optional[str],
    *,
    abstained: bool = False,
    expected_abstention: bool = False,
) -> Tuple[Optional[float], Optional[float]]:
    """Score a prediction against gold, including unanswerable abstention.

    Unanswerable items (expected_abstention, no gold string): EM/F1 are 1.0
    if the system abstained, else 0.0. Missing gold on an answerable item
    yields (None, None).
    """
    if expected_abstention and not (gold_answer and gold_answer.strip()):
        score = 1.0 if abstained else 0.0
        return score, score
    if gold_answer is None or not str(gold_answer).strip():
        return None, None
    return exact_match(prediction, gold_answer), token_f1(prediction, gold_answer)


def mixed_support_answer_gap(
    answer_f1: float,
    claim_labels: Sequence[VerificationLabel],
    *,
    f1_high: float = 0.7,
) -> bool:
    """True when answer-level F1 looks strong while gold claims are mixed.

    RQ3 diagnostic: a mixed-support answer can still match gold tokens.
    """
    assessable = [VerificationLabel(label.value) for label in claim_labels]
    if not assessable:
        return False
    n_supported = sum(1 for label in assessable if label == VerificationLabel.SUPPORTED)
    mixed = 0 < n_supported < len(assessable)
    return mixed and answer_f1 >= f1_high
