"""Dual-annotator IAA for verifier_eval-style claim–premise labels.

A second human rater is required for confirmatory IAA. This module does not
invent that rater. Incomplete rater-B files yield kappa=null.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from rageval.analysis.iaa_io import load_rater_labels
from rageval.metrics.agreement import summarize_agreement

SCHEMA = "rageval.iaa.v1"


def compare_raters(
    path_a: str,
    path_b: str,
) -> Dict[str, Any]:
    a_id, a_map = load_rater_labels(path_a)
    b_id, b_map = load_rater_labels(path_b)
    shared = sorted(set(a_map) & set(b_map))
    missing_a = sorted(set(b_map) - set(a_map))
    missing_b = sorted(set(a_map) - set(b_map))
    unlabeled_b = [i for i in shared if b_map[i] is None]
    unlabeled_a = [i for i in shared if a_map[i] is None]
    labeled = [i for i in shared if a_map[i] is not None and b_map[i] is not None]
    payload: Dict[str, Any] = {
        "schema": SCHEMA,
        "rater_a": a_id,
        "rater_b": b_id,
        "n_shared_ids": len(shared),
        "n_labeled_both": len(labeled),
        "missing_in_a": missing_a,
        "missing_in_b": missing_b,
        "unlabeled_in_a": unlabeled_a,
        "unlabeled_in_b": unlabeled_b,
        "complete": bool(labeled)
        and not unlabeled_a
        and not unlabeled_b
        and not missing_a
        and not missing_b,
        "percent_agreement": None,
        "cohen_kappa": None,
        "n_disagreements": 0,
        "disagreements": [],
        "note": (
            "Cohen's kappa is confirmatory IAA only when rater B is an independent human. "
            "A template or self-repeat is not a second annotator."
        ),
    }
    if not labeled:
        payload["note"] = (
            "Rater B has no labels on shared ids. Fill "
            "data/gold/iaa/annotator_b_verifier_eval_v1.json and re-run. "
            "kappa is undefined until then."
        )
        return payload
    summary = summarize_agreement(
        labeled,
        [a_map[i] for i in labeled],
        [b_map[i] for i in labeled],
    )
    payload.update(summary)
    if unlabeled_b or missing_b:
        payload["complete"] = False
        payload["note"] = (
            f"Partial overlap: {len(labeled)} labeled pairs. "
            "Treat kappa as diagnostic until rater B finishes the set."
        )
    return payload


def render_iaa_markdown(result: Dict[str, Any]) -> str:
    kappa = result.get("cohen_kappa")
    kappa_s = "null" if kappa is None else str(kappa)
    lines = [
        "# Inter-annotator agreement",
        "",
        f"**Rater A:** `{result.get('rater_a')}`. **Rater B:** `{result.get('rater_b')}`.",
        f"**Labeled both:** {result.get('n_labeled_both')} / shared {result.get('n_shared_ids')}.",
        f"**Complete:** {result.get('complete')}.",
        f"**Percent agreement:** {result.get('percent_agreement')}.",
        f"**Cohen's kappa:** {kappa_s}.",
        "",
        result.get("note") or "",
        "",
        "This is not Niu et al. 2024 RAGTruth. Labels measure evidence support.",
        "",
    ]
    if result.get("unlabeled_in_b"):
        lines.append(
            "Unlabeled in B: `" + "`, `".join(result["unlabeled_in_b"][:24]) + "`"
        )
        lines.append("")
    return "\n".join(lines)


def write_iaa_report(result: Dict[str, Any], output: str) -> str:
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    if output.endswith(".json"):
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
            f.write("\n")
        return output
    with open(output, "w", encoding="utf-8") as f:
        f.write(render_iaa_markdown(result))
    sidecar = os.path.splitext(output)[0] + ".json"
    with open(sidecar, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    return output


def export_rater_from_verifier_eval(
    gold_path: str,
    output_path: str,
    *,
    annotator_id: str,
    role: str,
) -> str:
    with open(gold_path, "r", encoding="utf-8") as f:
        gold = json.load(f)
    items = []
    for row in gold.get("items") or []:
        items.append(
            {
                "id": row["id"],
                "claim": row.get("claim"),
                "premise": row.get("premise"),
                "gold_label": row.get("gold_label"),
            }
        )
    payload = {
        "schema_version": SCHEMA,
        "annotator_id": annotator_id,
        "role": role,
        "source": gold_path,
        "items": items,
    }
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    return output_path


def export_rater_b_template(gold_path: str, output_path: str) -> str:
    with open(gold_path, "r", encoding="utf-8") as f:
        gold = json.load(f)
    items = [
        {
            "id": row["id"],
            "claim": row.get("claim"),
            "premise": row.get("premise"),
            "gold_label": None,
        }
        for row in gold.get("items") or []
    ]
    payload = {
        "schema_version": SCHEMA,
        "annotator_id": "rater_b_unfilled",
        "role": "rater_b",
        "source": gold_path,
        "notes": (
            "Independent human rater. Copy this file to annotator_b_verifier_eval_v1.json "
            "and fill gold_label. Do not copy rater A labels."
        ),
        "items": items,
    }
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    return output_path
