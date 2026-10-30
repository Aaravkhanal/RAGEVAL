"""Diagnostic per-example run comparison."""

from rageval.analysis.compare_runs import compare_per_example, render_compare_markdown


def test_compare_per_example_deltas():
    left = {
        "v1_001": {
            "query_id": "v1_001",
            "claim_support_rate": 0.0,
            "answer_f1": 0.5,
            "abstained": False,
            "scenario_type": "unanswerable",
        },
        "v1_002": {
            "query_id": "v1_002",
            "claim_support_rate": 1.0,
            "answer_f1": 0.8,
            "abstained": False,
            "scenario_type": "standard",
        },
    }
    right = {
        "v1_001": {
            "query_id": "v1_001",
            "claim_support_rate": 1.0,
            "answer_f1": 1.0,
            "abstained": True,
            "scenario_type": "unanswerable",
        },
        "v1_002": {
            "query_id": "v1_002",
            "claim_support_rate": 0.5,
            "answer_f1": 0.7,
            "abstained": False,
            "scenario_type": "standard",
        },
    }
    result = compare_per_example(left, right, left_name="mock", right_name="nvidia")
    assert result["n_shared"] == 2
    assert result["mean_delta_claim_support_rate"] == 0.25
    assert result["faith_improved"] == ["v1_001"]
    assert result["faith_worsened"] == ["v1_002"]
    assert result["abstain_gained"] == ["v1_001"]
    text = render_compare_markdown(result)
    assert "v1_001" in text
    assert "not a confirmatory ranking" in text
