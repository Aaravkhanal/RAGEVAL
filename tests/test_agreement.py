"""Cohen's kappa and IAA loaders. Incomplete rater B stays kappa=null."""

import json
from pathlib import Path

from rageval.analysis.iaa import compare_raters, export_rater_b_template, write_iaa_report
from rageval.core.labels import VerificationLabel
from rageval.metrics.agreement import cohen_kappa, percent_agreement, summarize_agreement


def test_kappa_perfect_with_class_variation():
    a = [
        VerificationLabel.SUPPORTED,
        VerificationLabel.UNSUPPORTED,
        VerificationLabel.CONTRADICTED,
    ]
    assert percent_agreement(a, a) == 1.0
    assert cohen_kappa(a, a) == 1.0


def test_kappa_undefined_when_chance_is_one():
    a = [VerificationLabel.SUPPORTED, VerificationLabel.SUPPORTED]
    assert cohen_kappa(a, a) is None


def test_kappa_empty_is_none():
    assert cohen_kappa([], []) is None
    assert percent_agreement([], []) == 0.0


def test_summarize_agreement_lists_disagreements():
    ids = ["ve_001", "ve_002"]
    a = ["supported", "unsupported"]
    b = ["supported", "contradicted"]
    summary = summarize_agreement(ids, a, b)
    assert summary["n"] == 2
    assert summary["n_disagreements"] == 1
    assert summary["disagreements"][0]["id"] == "ve_002"
    assert summary["cohen_kappa"] is not None


def test_filled_llm_rater_b_is_complete_and_disclosed():
    result = compare_raters(
        "data/gold/iaa/annotator_a_verifier_eval_v1.json",
        "data/gold/iaa/annotator_b_verifier_eval_v1.json",
    )
    assert result["complete"] is True
    assert result["n_labeled_both"] == 24
    assert result["cohen_kappa"] is not None
    assert "disclosed LLM" in result["note"] or "diagnostic" in result["note"].lower()
    assert "confirmatory human" in result["note"].lower() or "not confirmatory" in result["note"].lower()
    b = json.loads(Path("data/gold/iaa/annotator_b_verifier_eval_v1.json").read_text(encoding="utf-8"))
    assert b["annotator_id"] == "rater_b_llm_grok"
    assert "not copied" in b["notes"].lower() or "were not copied" in b["notes"].lower()
    assert all(row.get("gold_label") for row in b["items"])


def test_unfilled_rater_b_kappa_is_null(tmp_path):
    gold = "data/gold/verifier_eval_v1.json"
    template = tmp_path / "b.json"
    export_rater_b_template(gold, str(template))
    result = compare_raters(gold, str(template))
    assert result["cohen_kappa"] is None
    assert result["percent_agreement"] is None
    assert result["complete"] is False
    assert result["n_labeled_both"] == 0
    assert "kappa is undefined" in result["note"]
    out = write_iaa_report(result, str(tmp_path / "iaa.md"))
    text = Path(out).read_text(encoding="utf-8")
    assert "Cohen's kappa:** null" in text or "**Cohen's kappa:** null" in text
    sidecar = json.loads((tmp_path / "iaa.json").read_text(encoding="utf-8"))
    assert sidecar["cohen_kappa"] is None


def test_cli_iaa_template_prints_null_kappa(tmp_path):
    import subprocess
    import sys

    out = tmp_path / "iaa.md"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "rageval.cli",
            "iaa",
            "--rater-a",
            "data/gold/iaa/annotator_a_verifier_eval_v1.json",
            "--rater-b",
            "data/gold/iaa/annotator_b_template.json",
            "--output",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "kappa=None" in proc.stdout
    assert out.is_file()


def test_two_filled_raters_compute_kappa(tmp_path):
    a = {
        "schema_version": "rageval.iaa.v1",
        "annotator_id": "a",
        "items": [
            {"id": "x1", "gold_label": "supported"},
            {"id": "x2", "gold_label": "unsupported"},
            {"id": "x3", "gold_label": "contradicted"},
        ],
    }
    b = {
        "schema_version": "rageval.iaa.v1",
        "annotator_id": "b",
        "items": [
            {"id": "x1", "gold_label": "supported"},
            {"id": "x2", "gold_label": "unsupported"},
            {"id": "x3", "gold_label": "unsupported"},
        ],
    }
    pa = tmp_path / "a.json"
    pb = tmp_path / "b.json"
    pa.write_text(json.dumps(a), encoding="utf-8")
    pb.write_text(json.dumps(b), encoding="utf-8")
    result = compare_raters(str(pa), str(pb))
    assert result["complete"] is True
    assert result["n_labeled_both"] == 3
    assert result["cohen_kappa"] is not None
    assert result["n_disagreements"] == 1
