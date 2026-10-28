"""5-way collapse rule and dual-evidence retention."""

from rageval.core.config import EvaluatorConfig
from rageval.core.labels import LABEL_SCHEMA_VERSION, VerificationLabel
from rageval.evaluator.label_decision import decide_claim_label


def test_dual_evidence_partial_when_contradiction_is_not_dominant():
    label, explanation = decide_claim_label(0.55, 0.52, n_supporting=1, n_contradicting=1)
    assert label == VerificationLabel.PARTIALLY_SUPPORTED
    assert "Dual evidence" in explanation


def test_dual_evidence_contradicted_when_contradiction_wins():
    label, explanation = decide_claim_label(0.55, 0.81, n_supporting=1, n_contradicting=1)
    assert label == VerificationLabel.CONTRADICTED
    assert "supporting chunks retained" in explanation


def test_partial_from_mid_entailment():
    label, _ = decide_claim_label(0.40, 0.10, n_supporting=0, n_contradicting=0)
    assert label == VerificationLabel.PARTIALLY_SUPPORTED


def test_supported_and_unsupported():
    assert decide_claim_label(0.80, 0.05, 1, 0)[0] == VerificationLabel.SUPPORTED
    assert decide_claim_label(0.10, 0.10, 0, 0)[0] == VerificationLabel.UNSUPPORTED


def test_default_evaluator_refuses_silent_heuristic():
    cfg = EvaluatorConfig()
    assert cfg.method == "nli"
    assert cfg.allow_heuristic_fallback is False
    assert LABEL_SCHEMA_VERSION == "rageval.claim_labels.v1"
