"""Confidence calibration, Expected Calibration Error (ECE), and temperature scaling for NLI."""

from __future__ import annotations
from typing import List, Dict, Any
import numpy as np


class ConfidenceCalibrator:
    """Calculates calibration metrics (ECE, Brier Score) and applies temperature scaling

    to ensure NLI verifier confidence probabilities reflect empirical reliability.
    """

    @staticmethod
    def compute_ece(
        confidences: List[float],
        ground_truth_labels: List[int],
        num_bins: int = 10,
    ) -> Dict[str, Any]:
        """Calculates Expected Calibration Error (ECE) and Brier Score.

        ground_truth_labels: 1 if prediction was correct, 0 if error.
        """
        if not confidences or len(confidences) != len(ground_truth_labels):
            return {"ece": 0.0, "brier_score": 0.0, "bins": []}

        conf_arr = np.array(confidences)
        gt_arr = np.array(ground_truth_labels)
        n = len(conf_arr)

        bin_boundaries = np.linspace(0, 1, num_bins + 1)
        ece = 0.0
        bin_data = []

        for i in range(num_bins):
            b_low = bin_boundaries[i]
            b_high = bin_boundaries[i + 1]

            # In-bin indices
            in_bin = (conf_arr > b_low) & (conf_arr <= b_high) if i > 0 else (conf_arr >= b_low) & (conf_arr <= b_high)
            bin_size = np.sum(in_bin)

            if bin_size > 0:
                bin_acc = float(np.mean(gt_arr[in_bin]))
                bin_conf = float(np.mean(conf_arr[in_bin]))
                abs_diff = abs(bin_acc - bin_conf)
                ece += (bin_size / n) * abs_diff

                bin_data.append({
                    "bin_range": f"[{b_low:.1f}, {b_high:.1f}]",
                    "bin_size": int(bin_size),
                    "mean_accuracy": round(bin_acc, 4),
                    "mean_confidence": round(bin_conf, 4),
                    "abs_gap": round(abs_diff, 4),
                })

        brier = float(np.mean((conf_arr - gt_arr) ** 2))

        return {
            "ece": round(float(ece), 4),
            "brier_score": round(brier, 4),
            "num_samples": n,
            "bins": bin_data,
        }

    @staticmethod
    def apply_temperature_scaling(logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
        """Scales logits by temperature factor: Softmax(z / T)."""
        temp = max(temperature, 1e-4)
        scaled_logits = logits / temp
        exp_logits = np.exp(scaled_logits - np.max(scaled_logits, axis=-1, keepdims=True))
        return exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
