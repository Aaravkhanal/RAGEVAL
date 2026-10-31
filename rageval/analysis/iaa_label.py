"""Apply independent-human labels onto the rater-B IAA template.

This does not invent labels. A human supplies them via --set.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from rageval.core.labels import parse_verification_label

ALLOWED = (
    "supported",
    "partially_supported",
    "unsupported",
    "contradicted",
    "ambiguous",
)


def load_template(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_labels(
    payload: dict,
    labels: Dict[str, str],
    *,
    annotator_id: str = "rater_b_human",
) -> dict:
    out = dict(payload)
    out["annotator_id"] = annotator_id
    out["role"] = "rater_b"
    items = []
    unknown = sorted(set(labels) - {row.get("id") for row in payload.get("items") or []})
    if unknown:
        raise ValueError(f"Unknown claim ids: {', '.join(unknown)}")
    for row in payload.get("items") or []:
        item = dict(row)
        item_id = item.get("id")
        if item_id in labels:
            item["gold_label"] = parse_verification_label(labels[item_id]).value
        items.append(item)
    out["items"] = items
    return out


def unlabeled_ids(payload: dict) -> List[str]:
    ids = []
    for row in payload.get("items") or []:
        if not row.get("gold_label"):
            ids.append(str(row.get("id")))
    return ids


def write_rater(payload: dict, path: str) -> str:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    return path


def parse_set_flags(values: Optional[List[str]]) -> Dict[str, str]:
    labels: Dict[str, str] = {}
    for raw in values or []:
        if "=" not in raw:
            raise ValueError(f"--set must be id=label, got {raw!r}")
        item_id, label = raw.split("=", 1)
        item_id, label = item_id.strip(), label.strip()
        if not item_id:
            raise ValueError(f"--set missing id in {raw!r}")
        labels[item_id] = parse_verification_label(label).value
    return labels


def apply_and_write(
    template_path: str,
    output_path: str,
    set_flags: Optional[List[str]],
    *,
    annotator_id: str = "rater_b_human",
    force: bool = False,
) -> dict:
    """Apply supplied labels. Does not invent missing gold_label values."""
    payload = load_template(template_path)
    labels = parse_set_flags(set_flags)
    if not labels:
        remaining = unlabeled_ids(payload)
        return {
            "wrote": False,
            "path": None,
            "n_applied": 0,
            "unlabeled": remaining,
        }
    if os.path.exists(output_path) and not force:
        raise FileExistsError(
            f"{output_path} already exists. Pass --force to overwrite. "
            "Do not overwrite the disclosed LLM file annotator_b_verifier_eval_v1.json."
        )
    out = apply_labels(payload, labels, annotator_id=annotator_id)
    write_rater(out, output_path)
    return {
        "wrote": True,
        "path": output_path,
        "n_applied": len(labels),
        "unlabeled": unlabeled_ids(out),
        "annotator_id": annotator_id,
    }
