"""Confusion matrix and macro-F1 for verifier eval."""

from rageval.core.labels import VerificationLabel
from rageval.metrics.classification import accuracy, confusion_matrix, macro_f1, per_class_scores


def test_perfect_and_mixed_classification():
    gold = [
        VerificationLabel.SUPPORTED,
        VerificationLabel.UNSUPPORTED,
        VerificationLabel.CONTRADICTED,
        VerificationLabel.SUPPORTED,
    ]
    pred = [
        VerificationLabel.SUPPORTED,
        VerificationLabel.UNSUPPORTED,
        VerificationLabel.UNSUPPORTED,
        VerificationLabel.SUPPORTED,
    ]
    scores = per_class_scores(gold, pred)
    assert scores["supported"]["f1"] == 1.0
    assert scores["contradicted"]["recall"] == 0.0
    assert accuracy(gold, pred) == 0.75
    matrix = confusion_matrix(gold, pred)
    # gold contradicted (index 3) predicted unsupported (index 2)
    labels_index_unsupported = 2
    labels_index_contradicted = 3
    assert matrix[labels_index_contradicted][labels_index_unsupported] == 1
    assert macro_f1(scores) >= 0.0
