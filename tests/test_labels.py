"""Label alias loading for historical JSON."""

from rageval.core.labels import VerificationLabel, parse_verification_label
from rageval.core.schemas import GoldClaim
from rageval.core.config import pipeline_config_from_yaml


def test_historical_aliases():
    assert parse_verification_label("ENTAILEMENT") == VerificationLabel.SUPPORTED
    assert parse_verification_label("NEUTRAL") == VerificationLabel.UNSUPPORTED
    assert parse_verification_label("CONTRADICTION") == VerificationLabel.CONTRADICTED
    claim = GoldClaim(claim="x", status="ENTAILEMENT")
    assert claim.status == VerificationLabel.SUPPORTED


def test_yaml_pipeline_config_loads():
    cfg = pipeline_config_from_yaml("configs/smoke_heuristic_eval.yaml")
    assert cfg.evaluator.method == "heuristic"
    assert cfg.generator.backend == "mock"
