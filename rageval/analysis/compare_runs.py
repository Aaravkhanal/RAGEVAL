"""Compare two per_example.jsonl files on shared query ids. Diagnostic only."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional


METRIC_KEYS = (
    "claim_support_rate",
    "unsupported_claim_rate",
    "contradiction_rate",
    "recall_at_5",
    "mrr",
    "answer_f1",
    "answer_em",
)


def load_per_example(path: str, config_name: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if config_name and rec.get("config_name") != config_name:
                continue
            qid = rec.get("query_id")
            if not qid:
                continue
            rows[str(qid)] = rec
    return rows


def _delta(left: Any, right: Any) -> Optional[float]:
    try:
        return round(float(right) - float(left), 4)
    except (TypeError, ValueError):
        return None


def compare_per_example(
    left: Dict[str, Dict[str, Any]],
    right: Dict[str, Dict[str, Any]],
    *,
    left_name: str,
    right_name: str,
) -> Dict[str, Any]:
    shared = sorted(set(left) & set(right))
    rows: List[Dict[str, Any]] = []
    for qid in shared:
        a = left[qid]
        b = right[qid]
        rec: Dict[str, Any] = {
            "query_id": qid,
            "scenario_type": b.get("scenario_type") or a.get("scenario_type"),
            "left_abstained": bool(a.get("abstained")),
            "right_abstained": bool(b.get("abstained")),
        }
        for key in METRIC_KEYS:
            rec[f"left_{key}"] = a.get(key)
            rec[f"right_{key}"] = b.get(key)
            rec[f"delta_{key}"] = _delta(a.get(key), b.get(key))
        rows.append(rec)
    faith_deltas = [r["delta_claim_support_rate"] for r in rows if r["delta_claim_support_rate"] is not None]
    mean_delta = round(sum(faith_deltas) / len(faith_deltas), 4) if faith_deltas else None
    improved = [r["query_id"] for r in rows if (r.get("delta_claim_support_rate") or 0) > 0]
    worsened = [r["query_id"] for r in rows if (r.get("delta_claim_support_rate") or 0) < 0]
    abstain_gain = [
        r["query_id"]
        for r in rows
        if r["right_abstained"] and not r["left_abstained"]
    ]
    return {
        "left_name": left_name,
        "right_name": right_name,
        "n_shared": len(shared),
        "mean_delta_claim_support_rate": mean_delta,
        "n_faith_improved": len(improved),
        "n_faith_worsened": len(worsened),
        "faith_improved": improved,
        "faith_worsened": worsened,
        "abstain_gained": abstain_gain,
        "rows": rows,
        "note": (
            "Diagnostic per-item comparison. Items that share documents are not i.i.d. "
            "This is not a confirmatory ranking."
        ),
    }


def render_compare_markdown(result: Dict[str, Any]) -> str:
    lines = [
        f"# Run comparison: `{result.get('left_name')}` vs `{result.get('right_name')}`",
        "",
        result.get("note") or "",
        "",
        f"**Shared items:** {result.get('n_shared')}.",
        f"**Mean Δ claim_support_rate (right − left):** {result.get('mean_delta_claim_support_rate')}.",
        f"**Faith improved:** {result.get('n_faith_improved')}. **Worsened:** {result.get('n_faith_worsened')}.",
        "",
    ]
    gained = result.get("abstain_gained") or []
    if gained:
        lines.append("**Abstained on the right only:** `" + "`, `".join(gained) + "`.")
        lines.append("")
    worsened = result.get("faith_worsened") or []
    if worsened:
        lines.append("**Lower claim support on the right:** `" + "`, `".join(worsened) + "`.")
        lines.append("")
    lines.extend(
        [
            "| id | scenario | left faith | right faith | Δ faith | left F1 | right F1 | left abstain | right abstain |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in result.get("rows") or []:
        lines.append(
            f"| `{row['query_id']}` | {row.get('scenario_type') or ''} | "
            f"{row.get('left_claim_support_rate')} | {row.get('right_claim_support_rate')} | "
            f"{row.get('delta_claim_support_rate')} | {row.get('left_answer_f1')} | "
            f"{row.get('right_answer_f1')} | {row.get('left_abstained')} | {row.get('right_abstained')} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_compare_report(result: Dict[str, Any], output: str) -> str:
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    if output.endswith(".json"):
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
            f.write("\n")
        return output
    with open(output, "w", encoding="utf-8") as f:
        f.write(render_compare_markdown(result))
    sidecar = os.path.splitext(output)[0] + ".json"
    with open(sidecar, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    return output


def compare_files(
    left_path: str,
    right_path: str,
    *,
    left_config: Optional[str] = None,
    right_config: Optional[str] = None,
    left_name: Optional[str] = None,
    right_name: Optional[str] = None,
) -> Dict[str, Any]:
    left = load_per_example(left_path, left_config)
    right = load_per_example(right_path, right_config)
    return compare_per_example(
        left,
        right,
        left_name=left_name or left_config or left_path,
        right_name=right_name or right_config or right_path,
    )
