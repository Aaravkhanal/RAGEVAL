"""Human rater-B labeling helper. Does not invent labels."""

import json
from pathlib import Path

import pytest

from rageval.analysis.iaa_label import apply_and_write, parse_set_flags


def test_parse_set_flags_requires_equals():
    with pytest.raises(ValueError, match="id=label"):
        parse_set_flags(["ve_001 supported"])
    labels = parse_set_flags(["ve_001=supported", "ve_002=contradicted"])
    assert labels == {"ve_001": "supported", "ve_002": "contradicted"}


def test_apply_and_write_does_not_invent_or_overwrite(tmp_path):
    template = Path("data/gold/iaa/annotator_b_template.json")
    out = tmp_path / "annotator_b_human.json"
    listed = apply_and_write(str(template), str(out), None)
    assert listed["wrote"] is False
    assert "ve_001" in listed["unlabeled"]
    assert not out.exists()

    written = apply_and_write(
        str(template),
        str(out),
        ["ve_001=supported"],
        annotator_id="rater_b_human",
    )
    assert written["wrote"] is True
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["annotator_id"] == "rater_b_human"
    by_id = {row["id"]: row["gold_label"] for row in payload["items"]}
    assert by_id["ve_001"] == "supported"
    assert by_id["ve_002"] is None
    assert "ve_002" in written["unlabeled"]

    with pytest.raises(FileExistsError):
        apply_and_write(str(template), str(out), ["ve_002=unsupported"])

    apply_and_write(
        str(template),
        str(out),
        ["ve_001=supported", "ve_002=unsupported"],
        force=True,
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    by_id = {row["id"]: row["gold_label"] for row in payload["items"]}
    assert by_id["ve_002"] == "unsupported"


def test_cli_iaa_label_set(tmp_path):
    import subprocess
    import sys

    out = tmp_path / "human.json"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "rageval.cli",
            "iaa-label",
            "--template",
            "data/gold/iaa/annotator_b_template.json",
            "--output",
            str(out),
            "--set",
            "ve_001=supported",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["items"][0]["gold_label"] == "supported"
    assert payload["items"][1]["gold_label"] is None
