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


def describe_generator(metrics: Dict[str, Any]) -> str:
    """Describe the generator from recorded pipeline identity. Default is the blinded mock."""
    pipes = [p for p in (metrics.get("pipelines") or []) if isinstance(p, dict)]
    backends = [str(p.get("generator_backend") or "") for p in pipes]
    models = [str(p.get("generator_model") or "") for p in pipes]
    live = [b for b in backends if b and b != "mock"]
    if live:
        uniq_b = sorted(set(live))
        uniq_m = sorted({m for m, b in zip(models, backends) if b != "mock" and m})
        bits = f"live generator backend {', '.join(uniq_b)}"
        if uniq_m:
            bits += f" (model {', '.join(uniq_m)})"
        return bits + "."
    names = list(metrics.get("by_config") or {})
    exp = str(metrics.get("experiment_id") or "")
    if any("NVIDIA" in n for n in names) or "nvidia" in exp.lower():
        return "live NVIDIA NIM OpenAI-compatible HTTP generator."
    return "blinded mock (`faithful`, abstain only on empty retrieval)."


def describe_verifier(metrics: Dict[str, Any]) -> str:
    pipes = [p for p in (metrics.get("pipelines") or []) if isinstance(p, dict)]
    methods = [str(p.get("evaluator_method") or "") for p in pipes if p.get("evaluator_method")]
    if methods and all(m == "heuristic" for m in methods):
        return "lexical heuristic (`allow_heuristic_fallback=false`)."
    if methods and all(m == "nli" for m in methods):
        return "DeBERTa-v3 NLI (`allow_heuristic_fallback=false`)."
    if methods:
        return "verifier methods: " + ", ".join(sorted(set(methods))) + "."
    return "DeBERTa-v3 NLI (`allow_heuristic_fallback=false`)."


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
    n_documents = metrics.get("n_documents")
    configs = metrics.get("by_config") or {}
    baseline = "Dense_Chunk256_Baseline"
    exp_id = metrics.get("experiment_id") or ""
    if exp_id == "A_chunk":
        tables_rel = "reports/phase7/A_chunk_overlap32"
    elif exp_id == "nvidia_nim_retrieve":
        tables_rel = "reports/phase7/nvidia_nim_retrieve"
    elif exp_id == "nvidia_nim_v1" or "nvidia" in exp_id.lower():
        tables_rel = "reports/phase7/nvidia_nim_v1"
    elif version.startswith("1.2"):
        tables_rel = "reports/phase7/v1_2_matrix"
    elif version.startswith("1.1"):
        tables_rel = "reports/phase7/v1_1_matrix"
    else:
        tables_rel = "reports/phase7/v1_matrix"
    size_bits = [f"`{dataset_id}` {version}", f"n={n_items}"]
    if n_documents is not None:
        size_bits.append(f"{n_documents} documents")
    lines: List[str] = [
        f"# Findings — run `{run_id}`",
        "",
        f"**Label:** `{label}`. **Dataset:** {', '.join(size_bits)}.",
        f"**Source:** `metrics.json` for run `{run_id}`.",
        "Every number below traces to that run or to a named companion file.",
        "Negative and inconclusive results are in scope. No overall score. No ranking claim.",
        "",
        "## What this run is",
        "",
        f"- Generator: {describe_generator(metrics)}",
        f"- Verifier: {describe_verifier(metrics)}",
        "- Cost: null (no pricing_source).",
        "- Items share documents, so they are not i.i.d. Bootstrap CIs are diagnostic.",
        f"- Confirmatory tests require n≥30 i.i.d. This run has n={n_items}.",
    ]
    if version.startswith("1.1") or version.startswith("1.2"):
        lines.append(
            "- Companion to the published v1.0.0 tables "
            "(`20261028T183042Z_a97ad68f`). It does not replace them."
        )
    lines.extend(
        [
            "",
            "## RQ1 — retrieval family, chunk size, rerank",
            "",
        ]
    )
    recalls = {name: _mean(block, "recall_at_5") for name, block in configs.items()}
    mrrs = {name: _mean(block, "mrr") for name, block in configs.items()}
    faiths = {name: _mean(block, "claim_support_rate") for name, block in configs.items()}
    unique_r5 = set(recalls.values())
    unique_mrr = set(mrrs.values())
    if len(unique_r5) == 1:
        r5 = next(iter(unique_r5))
        if "Hybrid_RRF_Chunk256" in configs or "Hybrid_RRF_Reranked" in configs:
            hypo = (
                "The RQ1 hypothesis that hybrid RRF improves Recall@5 "
                "vs dense-only is **falsified on this corpus** (the means are equal)."
            )
        else:
            hypo = (
                "Chunk-size differences on Recall@5 are **not identifiable** "
                "on this corpus (the means are equal)."
            )
        lines.append(
            f"- Recall@5 is **identical** at {r5} on all {len(configs)} configs "
            f"(run `{run_id}`). {hypo}"
        )
    else:
        lines.append(
            "- Recall@5 by config: "
            + ", ".join(f"{name}={value}" for name, value in recalls.items())
            + "."
        )
    if len(unique_mrr) == 1:
        lines.append(f"- MRR is identical at {next(iter(unique_mrr))}.")
    else:
        lines.append(
            "- MRR by config: "
            + ", ".join(f"{name}={value}" for name, value in mrrs.items())
            + "."
        )
    faith_bits = []
    for key in (baseline, "Hybrid_RRF_Chunk256", "Hybrid_RRF_Reranked"):
        if key in faiths and faiths[key] is not None:
            faith_bits.append(f"{faiths[key]} on {key}")
    if not faith_bits:
        faith_bits = [f"{value} on {name}" for name, value in faiths.items() if value is not None]
    elif len(faith_bits) == 1 and len(faiths) > 1:
        faith_bits = [f"{value} on {name}" for name, value in faiths.items() if value is not None]
    if faith_bits:
        lines.append("- Claim support (faithfulness) is " + ", ".join(faith_bits) + ".")
    hybrid_lift = recall_relative_lift_pct(metrics, baseline, "Hybrid_RRF_Chunk256")
    if hybrid_lift is not None:
        lines.append(
            f"- Computed relative Recall@5 lift, Hybrid_RRF_Chunk256 vs {baseline}: "
            f"{hybrid_lift:.1f}%."
        )
    if len(unique_r5) == 1 and len(unique_mrr) == 1:
        rq1_close = (
            "- **Conclusion:** RQ1 retrieval differences are **not identifiable** "
            "at this n and corpus size."
        )
    elif len(unique_r5) == 1:
        rq1_close = (
            "- **Conclusion:** Recall@5 remains identical, so an RQ1 Recall@5 ranking "
            "is still not identifiable. MRR differs across configs; n is underpowered "
            "and items share documents, so that difference is diagnostic only."
        )
    else:
        rq1_close = (
            "- **Conclusion:** Retrieval metrics differ across configs on this run; "
            "n is underpowered and items share documents, so this is not a confirmatory ranking."
        )
    lines.extend(
        [
            f"- Significance vs baseline is in `{tables_rel}/significance.json`. "
            "Comparisons stay diagnostic unless n≥30 i.i.d.; recorded items share documents, "
            "so `underpowered=true` and `is_significant=false`.",
            rq1_close,
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
        mixed_n = mixed_rows[0][1]
        claim_vals = {row[3] for row in mixed_rows}
        if len(f1s) == 1 and len(claim_vals) > 1:
            lines.append(
                "- That is the RQ3 pattern on this slice: answer-level F1 does not move; "
                f"claim support does. n={mixed_n} is too small to confirm the hypothesis beyond this pilot."
            )
        elif len(f1s) == 1:
            lines.append(
                "- On this slice both token F1 and claim support are identical across configs. "
                f"n={mixed_n} is too small to confirm RQ3 beyond this pilot."
            )
        else:
            lines.append(
                "- Mixed-support token F1 also differs across configs. "
                f"n={mixed_n} is too small to confirm RQ3 beyond this pilot."
            )
    lines.extend(
        [
            "",
            "## RQ4 — unanswerable / conflicting under a blinded generator",
            "",
        ]
    )
    def _round4(value):
        return round(float(value), 4) if isinstance(value, (int, float)) else value

    abst = {name: _round4(block.get("abstention_accuracy")) for name, block in configs.items()}
    unique_abst = set(abst.values())
    if len(unique_abst) == 1:
        lines.append(
            f"- Ablation abstention accuracy is **{next(iter(unique_abst))}** "
            f"on all {len(configs)} configs (run `{run_id}`)."
        )
    elif abst:
        lines.append(f"- Abstention accuracy by config: {abst}.")
    empty_ns = []
    for block in configs.values():
        empty = (block.get("by_scenario") or {}).get("empty_context") or {}
        if empty:
            empty_ns.append(
                (empty.get("n"), empty.get("abstention_accuracy"), empty.get("recall_at_5"))
            )
    if empty_ns:
        n_empty, empty_abst, empty_r5 = empty_ns[0]
        lines.append(
            f"- Empty-context slice n={n_empty}: retrieval is dropped before generate "
            f"(recall@5={empty_r5}); mock abstention_accuracy={empty_abst}."
        )
    lines.extend(
        [
            "- Other unanswerable items still retrieve context; the mock copies sentences and does not "
            "see `test_type` (`tests/test_generator_blind.py`).",
            "- A pre-blind historical smoke run had abstention 1.0 because the mock saw UNANSWERABLE. "
            "Gold-label leakage was driving that abstention.",
            "- Conflicting items: the mock copies one retrieved document and does not hedge "
            "(see case `v1_017` when present).",
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
        ]
    )
    if version.startswith("1.0") or n_items == 24:
        lines.append(
            f"- n={n_items} items / {n_documents or 16} documents; "
            "v1.1.0 items `v1_025`–`v1_028` are unscored in this run."
        )
    else:
        lines.append(
            f"- n={n_items} items / {n_documents or '?'} documents. "
            "Still underpowered (confirmatory n≥30 i.i.d.)."
        )
    lines.extend(
        [
            "- Single-author gold. No IAA.",
        ]
    )
    if exp_id == "A_chunk":
        lines.append("- Dense chunk overlap in this run was fixed at 32 (A_chunk protocol).")
    else:
        lines.append(
            "- Dense chunk overlap in this run was 16/32/64, not the Phase 7 A_chunk fixed-32 protocol."
        )
    if version.startswith("1.2"):
        error_line = "- Errors: `reports/error_analysis_v1_2.md`"
    elif version.startswith("1.1"):
        error_line = "- Errors: `reports/error_analysis_v1_1.md`"
    else:
        error_line = "- Errors: `reports/error_analysis_phase6.md`"
    lines.extend(
        [
            "- Faithfulness is support-by-retrieved-evidence, not world truth.",
            "- This project is not Niu et al. 2024 RAGTruth.",
            "",
            "## Files",
            "",
            f"- Run id: `{run_id}`",
            f"- Tables: `{tables_rel}/metrics.json`",
            error_line,
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
