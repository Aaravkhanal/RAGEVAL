"""Load rater JSON: verifier_eval gold or rageval.iaa.v1 files."""

from __future__ import annotations

import json
from typing import Dict, Optional, Tuple

from rageval.core.labels import parse_verification_label


def load_rater_labels(path: str) -> Tuple[str, Dict[str, Optional[str]]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    annotator = (
        data.get("annotator_id")
        or data.get("annotator")
        or data.get("dataset_id")
        or path
    )
    mapping: Dict[str, Optional[str]] = {}
    for row in data.get("items") or []:
        item_id = row.get("id")
        if not item_id:
            continue
        raw = row.get("gold_label")
        if raw is None or raw == "":
            mapping[item_id] = None
            continue
        mapping[item_id] = parse_verification_label(raw).value
    return str(annotator), mapping
