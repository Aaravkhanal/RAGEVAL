from rageval.evaluator.lexical import score


def test_new_numeric_relation_conflict_and_unrelated_number():
    assert score('Orion revenue was $730 million in 2026.','Orion revenue was $12 million in 2026.')['contradiction'] > .6
    assert score('Orion revenue was $730 million in 2026.','Orion has offices in 44 countries.')['neutral'] > .6


def test_negation_is_symmetric_and_not_a_trigger_word():
    assert score('The service does not contain personal identifiers.','The service contains personal identifiers.')['contradiction'] > .6
    assert score('The legacy product was discontinued.','The legacy product was discontinued.')['entailment'] > .5
    assert score('The birds are migratory.','An unrelated product was discontinued.')['neutral'] > .6


def test_mixed_clauses_are_partial():
    result=score('Orion revenue was $730 million. Customer churn was 2%.','Orion revenue was $730 million and customer churn was 8%.')
    assert .3 <= result['entailment'] < .5


def test_location_qualifiers_do_not_contradict_shorter_supported_location():
    assert score('The probe landed in Ocean Basin at site 7.', 'The probe landed in Ocean Basin.')['entailment']>.5
    assert score('The probe landed in Ocean Basin at site 7.', 'The probe landed in Desert Valley.')['contradiction']>.6
