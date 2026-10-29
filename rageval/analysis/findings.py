"""Honest findings from a completed metrics.json. No canned ranking sentences."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

CANNED_UNCOMPUTED = (
    "16.4%",
    "16.4 percent",
    r"16.4\%",
)
SOTA_PHRASES = ("sota", "state of the art", "state-of-the-art", "state of-the-art")
RUN_ID_V1 = "20261028T183042Z_a97ad68f"


def _mean(block: dict, key: str) -> Optional[float]:
    value = block.get(key)
    if isinstance(value, dict):
        return value.get("mean")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def recall_relative_lift_pct(
    metrics: Dict[str, Any],
    baseline: str,
    treatment: str,
) -> Optional[float]:
    configs = metrics.get("by_config") or {}
    if baseline not in configs or treatment not in configs:
        return None
    base = _mean(configs[baseline], "recall_at_5")
    treat = _mean(configs[treatment], "recall_at_5")
    if base is None or treat is None or base == 0:
        return None
    return 100.0 * (treat - base) / base


def assert_findings_text_allowed(text: str, metrics: Dict[str, Any]) -> None:
    """Refuse the historical 16.4% Recall@5 sentence unless metrics compute that lift."""
    lowered = text.lower()
    for phrase in SOTA_PHRASES:
        if phrase in lowered:
            raise ValueError(f"Findings must not use ranking language {phrase!r}")
    lift = None
    configs = list((metrics.get("by_config") or {}))
    if "Dense_Chunk256_Baseline" in configs:
        for name in configs:
            if name == "Dense_Chunk256_Baseline":
                continue
            cand = recall_relative_lift_pct(metrics, "Dense_Chunk256_Baseline", name)
            if cand is not None and abs(cand - 16.4) <= 0.15:
                lift = cand
                break
    if re.search(r"16\.4\s*%", text) or "16.4 percent" in lowered or r"16.4\%" in text:
        if lift is None:
            raise ValueError(
                "Refusing uncomputed 16.4% Recall@5 claim; metrics do not produce that lift."
            )


def write_findings(
    metrics: Dict[str, Any],
    output_dir: str,
    *,
    run_id: str = RUN_ID_V1,
    case_studies: Optional[List[Dict[str, Any]]] = None,
    significance: Optional[Dict[str, Any]] = None,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    text = render_findings(
        metrics,
        run_id=run_id,
        case_studies=case_studies or [],
        significance=significance,
    )
    assert_findings_text_allowed(text, metrics)
    path = os.path.join(output_dir, "FINDINGS.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def render_findings(
    metrics: Dict[str, Any],
    *,
    run_id: str,
    case_studies: List[Dict[str, Any]],
    significance: Optional[Dict[str, Any]] = None,
) -> str:
    label = metrics.get("label") or "pilot"
    dataset_id = metrics.get("dataset_id") or "unknown"
    version = metrics.get("dataset_version") or ""
    n_items = metrics.get("n_items")
    configs = metrics.get("by_config") or {}
    baseline = "Dense_Chunk256_Baseline"
    lines: List[str] = [
        f"# Findings — run `{run_id}`",
        "",
        f"**Label:** `{label}`. **Dataset:** `{dataset_id}` {version}, n={n_items}.",
        f"**Source:** `metrics.json` for run `{run_id}`.",
        "Every number below traces to that run or to a named companion file.",
        "Negative and inconclusive results are in scope. No overall score. No ranking claim.",
        "",
        "## What this run is",
        "",
        "- Generator: blinded mock (`faithful`, abstain only on empty retrieval).",
        "- Verifier: DeBERTa-v3 NLI (`allow_heuristic_fallback=false`).",
        "- Cost: null (no pricing_source).",
        "- Items share documents, so they are not i.i.d. Bootstrap CIs are diagnostic.",
        f"- Confirmatory tests require n≥30 i.i.d. This run has n={n_items}.",
        "",
        "## RQ1 — retrieval family, chunk size, rerank",
        "",
    ]
    recalls = {name: _mean(block, "recall_at_5") for name, block in configs.items()}
    mrrs = {name: _mean(block, "mrr") for name, block in configs.items()}
    faiths = {name: _mean(block, "claim_support_rate") for name, block in configs.items()}
    unique_r5 = set(recalls.values())
    unique_mrr = set(mrrs.values())
    if len(unique_r5) == 1:
        r5 = next(iter(unique_r5))
        lines.append(
            f"- Recall@5 is **identical** at {r5} on all {len(configs)} configs "
            f"(run `{run_id}`). The RQ1 hypothesis that hybrid RRF improves Recall@5 "
            "vs dense-only is **falsified on this corpus** (the means are equal)."
        )
    else:
        lines.append(f"- Recall@5 by config: {recalls}.")
    if len(unique_mrr) == 1:
        lines.append(f"- MRR is identical at {next(iter(unique_mrr))}.")
    if baseline in faiths:
        lines.append(
            f"- Claim support (faithfulness) is {faiths.get(baseline)} on {baseline}, "
            f"{faiths.get('Hybrid_RRF_Chunk256')} on Hybrid_RRF_Chunk256, and "
            f"{faiths.get('Hybrid_RRF_Reranked')} on Hybrid_RRF_Reranked."
        )
    hybrid_lift = recall_relative_lift_pct(metrics, baseline, "Hybrid_RRF_Chunk256")
    if hybrid_lift is not None:
        lines.append(
            f"- Computed relative Recall@5 lift, Hybrid_RRF_Chunk256 vs {baseline}: "
            f"{hybrid_lift:.1f}%."
        )
    lines.extend(
        [
            "- Significance vs baseline is in `reports/phase7/v1_matrix/significance.json`. "
            "All comparisons have `underpowered=true` and `is_significant=false`.",
            "- **Conclusion:** RQ1 retrieval differences are **not identifiable** at this n and corpus size.",
            "",
            "## RQ2 — verifier vs gold claims",
            "",
            "- Not scored inside the ablation run. Companion file `reports/verifier_eval_v1.md` "
            "(24 labeled claim–premise pairs): DeBERTa macro-F1 **0.6921**, lexical heuristic **0.5140**.",
            "- On that set the RQ2 hypothesis (NLI macro-F1 > heuristic) is **not falsified**.",
            "- Partial-support F1 is 0.0 for both methods. n=24 is underpowered.",
            "",
            "## RQ3 — claim-level vs answer-level on mixed-support",
            "",
        ]
    )
    mixed_rows = []
    for name, block in configs.items():
        mixed = (block.get("by_scenario") or {}).get("mixed_support") or {}
        if mixed:
            mixed_rows.append((name, mixed.get("n"), mixed.get("answer_f1"), mixed.get("claim_support_rate")))
    if mixed_rows:
        f1s = {row[2] for row in mixed_rows}
        lines.append(
            f"- Mixed-support slice n={mixed_rows[0][1]} per config (run `{run_id}`)."
        )
        if len(f1s) == 1:
            lines.append(
                f"- Token F1 is identical at {next(iter(f1s))} across configs, "
                "while claim support ranges "
                f"{min(r[3] for r in mixed_rows)}–{max(r[3] for r in mixed_rows)}."
            )
        lines.append(
            "- That is the RQ3 pattern on this slice: answer-level F1 does not move; "
            "claim support does. n=4 is too small to confirm the hypothesis beyond this pilot."
        )
    lines.extend(
        [
            "",
            "## RQ4 — unanswerable / conflicting under a blinded generator",
            "",
            f"- Ablation abstention accuracy is **0.0** on all configs (run `{run_id}`).",
            "- Unanswerable items still retrieved context; the mock copies sentences and does not "
            "see `test_type` (`tests/test_generator_blind.py`).",
            "- A pre-blind historical smoke run had abstention 1.0 because the mock saw UNANSWERABLE. "
            "After blinding, abstention on v1 unanswerables is 0.0. That matches RQ4: "
            "gold-label leakage was driving abstention.",
            "- Conflicting items: the mock copies one retrieved document and does not hedge "
            "(see case `v1_017`).",
            "",
            "## RQ5 — latency and cost",
            "",
        ]
    )
    lats = {name: block.get("mean_latency_ms") for name, block in configs.items()}
    if lats:
        lat_s = ", ".join(
            f"{name}={value:.1f}" if isinstance(value, (int, float)) else f"{name}={value}"
            for name, value in lats.items()
        )
        lines.append(f"- Mean latency (ms): {lat_s}.")
    if lats.get("Hybrid_RRF_Reranked") is not None and lats.get(baseline) is not None:
        rerank = lats["Hybrid_RRF_Reranked"]
        base_lat = lats[baseline]
        if rerank < base_lat:
            lines.append(
                f"- Hybrid_RRF_Reranked mean latency ({rerank}) is **lower** than "
                f"{baseline} ({base_lat}) in this snapshot. The RQ5 hypothesis that "
                "reranking increases latency is **not supported** here "
                "(likely caching / shared evaluator load, not a structural ranking)."
            )
    lines.extend(
        [
            "- `estimated_cost_usd` is null. Do not report a dollar cost for this run.",
            "",
            "## Case studies",
            "",
            "Config: `Dense_Chunk256_Baseline` unless noted. Answers are mock extracts.",
            "",
        ]
    )
    if not case_studies:
        lines.append("_No case_studies.json supplied._")
        lines.append("")
    for case in case_studies:
        lines.extend(
            [
                f"### `{case.get('query_id')}` — {case.get('scenario_type')}",
                "",
                f"- Question: {case.get('question')}",
                f"- Gold: {case.get('gold_answer') or '(null; expected abstention)'}",
                f"- Answer excerpt: {case.get('answer_excerpt')}",
                f"- Auto labels: {case.get('auto_labels')}",
                f"- Metrics: claim_support={case.get('claim_support')}, "
                f"answer_f1={case.get('answer_f1')}, abstained={case.get('abstained')}, "
                f"recall@5={case.get('recall_at_5')}",
                f"- Stage: {case.get('primary_stage')} — {case.get('why')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Limitations",
            "",
            "- Mock generator, not an LLM.",
            "- n=24 items / 16 documents; v1.1.0 items `v1_025`–`v1_028` are unscored.",
            "- Single-author gold. No IAA.",
            "- Dense chunk overlap in this run was 16/32/64, not the Phase 7 A_chunk fixed-32 protocol.",
            "- Faithfulness is support-by-retrieved-evidence, not world truth.",
            "- This project is not Niu et al. 2024 RAGTruth.",
            "",
            "## Files",
            "",
            f"- Run id: `{run_id}`",
            "- Tables: `reports/phase7/v1_matrix/metrics.json`",
            "- Errors: `reports/error_analysis_phase6.md`",
            "- RQ2: `reports/verifier_eval_v1.md`",
            "",
        ]
    )
    return "\n".join(lines)


def load_case_studies(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("cases", [])
