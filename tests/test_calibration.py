"""Unit tests for confidence calibration (ECE) and temperature scaling."""

import numpy as np
from ragtruth.analysis.calibration import ConfidenceCalibrator


def test_ece_computation():
    confidences = [0.95, 0.90, 0.85, 0.80, 0.40, 0.35, 0.30]
    ground_truth = [1, 1, 1, 0, 0, 0, 1]

    calib = ConfidenceCalibrator.compute_ece(confidences, ground_truth, num_bins=5)
    assert "ece" in calib
    assert "brier_score" in calib
    assert 0.0 <= calib["ece"] <= 1.0
    assert calib["num_samples"] == len(confidences)


def test_temperature_scaling():
    logits = np.array([[2.0, 1.0, 0.0], [0.5, 2.5, 0.1]])
    scaled_probs = ConfidenceCalibrator.apply_temperature_scaling(logits, temperature=2.0)

    assert scaled_probs.shape == logits.shape
    assert np.allclose(np.sum(scaled_probs, axis=-1), 1.0)
    # Higher temperature softens distribution: max prob at T=2 should be less than at T=1
    unscaled_probs = ConfidenceCalibrator.apply_temperature_scaling(logits, temperature=1.0)
    assert np.max(scaled_probs[0]) < np.max(unscaled_probs[0])
