"""Answer-level EM/F1 and RQ3 mixed-support gap."""

from rageval.core.labels import VerificationLabel
from rageval.metrics.answer import (
    answer_em_f1,
    exact_match,
    mixed_support_answer_gap,
    token_f1,
)


def test_exact_match_normalizes_articles_and_punctuation():
    assert exact_match("The Eagle landed in the Sea of Tranquility.", "eagle landed in sea of tranquility") == 1.0
    assert exact_match("HarborNet reported $412 million", "HarborNet reported $500 million") == 0.0


def test_token_f1_partial_overlap():
    gold = (
        "Influenza A and B viruses cause seasonal epidemics of disease in people "
        "almost every winter in the United States."
    )
    mixed = gold + " Influenza D viruses also cause seasonal epidemics in people."
    score = token_f1(mixed, gold)
    assert score > 0.7
    assert score < 1.0


def test_unanswerable_abstention_scores():
    em, f1 = answer_em_f1("I cannot answer.", None, abstained=True, expected_abstention=True)
    assert em == 1.0 and f1 == 1.0
    em, f1 = answer_em_f1("Apollo launched in 1969.", None, abstained=False, expected_abstention=True)
    assert em == 0.0 and f1 == 0.0


def test_rq3_mixed_support_high_f1_low_claim_purity():
    gold = "HarborNet reported subscription revenue of $412 million for the second quarter of 2025."
    mixed = gold + " HarborNet employed 48,000 people in Osaka."
    f1 = token_f1(mixed, gold)
    labels = [VerificationLabel.SUPPORTED, VerificationLabel.UNSUPPORTED]
    assert mixed_support_answer_gap(f1, labels) is True
    assert mixed_support_answer_gap(1.0, [VerificationLabel.SUPPORTED, VerificationLabel.SUPPORTED]) is False
