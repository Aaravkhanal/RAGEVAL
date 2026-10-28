"""Per-class precision/recall/F1 and confusion matrices for verifier eval (RQ2)."""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

from rageval.core.labels import EVAL_LABEL_ORDER, VerificationLabel, parse_verification_label


def _as_label(value: VerificationLabel | str) -> VerificationLabel:
    return parse_verification_label(value)


def confusion_matrix(
    y_true: Sequence[VerificationLabel | str],
    y_pred: Sequence[VerificationLabel | str],
    labels: Sequence[VerificationLabel] = EVAL_LABEL_ORDER,
) -> List[List[int]]:
    """Rows = gold, columns = predicted, in `labels` order."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    index = {label: i for i, label in enumerate(labels)}
    matrix = [[0 for _ in labels] for _ in labels]
    for gold, pred in zip(y_true, y_pred):
        gi = index.get(_as_label(gold))
        pi = index.get(_as_label(pred))
        if gi is None or pi is None:
            continue
        matrix[gi][pi] += 1
    return matrix


def per_class_scores(
    y_true: Sequence[VerificationLabel | str],
    y_pred: Sequence[VerificationLabel | str],
    labels: Sequence[VerificationLabel] = EVAL_LABEL_ORDER,
) -> Dict[str, Dict[str, float]]:
    """Precision, recall, F1, support per label. Undefined scores are 0.0 when support and predictions are 0."""
    matrix = confusion_matrix(y_true, y_pred, labels)
    scores: Dict[str, Dict[str, float]] = {}
    for i, label in enumerate(labels):
        tp = matrix[i][i]
        fp = sum(matrix[r][i] for r in range(len(labels)) if r != i)
        fn = sum(matrix[i][c] for c in range(len(labels)) if c != i)
        support = sum(matrix[i])
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        scores[label.value] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": float(support),
        }
    return scores


def macro_f1(scores: Dict[str, Dict[str, float]], labels: Iterable[VerificationLabel] = EVAL_LABEL_ORDER) -> float:
    values = [scores[label.value]["f1"] for label in labels if label.value in scores]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def accuracy(y_true: Sequence[VerificationLabel | str], y_pred: Sequence[VerificationLabel | str]) -> float:
    if not y_true:
        return 0.0
    n = len(y_true)
    correct = sum(1 for gold, pred in zip(y_true, y_pred) if _as_label(gold) == _as_label(pred))
    return round(correct / n, 4)
