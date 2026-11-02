"""Independent review export must not invent human labels."""

import json
from pathlib import Path

from scripts.export_claim_review import export_review


def test_claim_review_export_is_blinded(tmp_path):
    source = Path("reports/phase7/live_matrix_v1/summaries.json")
    output = tmp_path / "review.jsonl"
    assert export_review(source, "Dense_Chunk256_Baseline", output) == 40
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(rows) == 40
    assert all(row["human_claim_spans"] is None for row in rows)
    assert all(row["human_support_labels"] is None for row in rows)
    assert all(row["human_citation_labels"] is None for row in rows)
    assert all("verifications" not in row for row in rows)
