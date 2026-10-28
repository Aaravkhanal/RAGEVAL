"""Gold comparison harness on verifier_eval_v1 using the lexical heuristic."""

from rageval.evaluator.gold_eval import evaluate_verifier_on_gold, load_verifier_eval


def test_verifier_eval_v1_loads_and_heuristic_harness_runs():
    payload = load_verifier_eval("data/gold/verifier_eval_v1.json")
    assert payload["schema_version"] == "rageval.verifier_eval.v1"
    assert len(payload["items"]) == 24
    labels = {item["gold_label"] for item in payload["items"]}
    assert "supported" in labels
    assert "contradicted" in labels
    assert "unsupported" in labels
    assert "partially_supported" in labels
    assert "ambiguous" in labels

    result = evaluate_verifier_on_gold(
        "data/gold/verifier_eval_v1.json",
        method="heuristic",
    )
    assert result["n"] == 24
    assert result["method"] == "heuristic"
    assert len(result["predictions"]) == 24
    assert "macro_f1" in result
    abstain = next(row for row in result["predictions"] if row["id"] == "ve_023")
    assert abstain["pred"] == "ambiguous"
    assert abstain["correct"] is True
