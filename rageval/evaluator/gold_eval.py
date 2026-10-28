"""Compare a verifier against a human-labeled claim set (RQ2)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from rageval.core.config import EvaluatorConfig
from rageval.core.labels import EVAL_LABEL_ORDER, VerificationLabel, parse_verification_label
from rageval.core.schemas import AtomicClaim, Chunk, RetrievedChunk
from rageval.evaluator.nli_verifier import NLIVerifier
from rageval.metrics.classification import accuracy, confusion_matrix, macro_f1, per_class_scores


def load_verifier_eval(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _premise_chunk(item: Dict[str, Any], index: int) -> RetrievedChunk:
    text = item["premise"]
    doc_id = item.get("source_doc_id") or f"gold_doc_{index}"
    chunk_id = item.get("chunk_id") or f"gold_chk_{index}"
    return RetrievedChunk(
        chunk=Chunk(
            id=chunk_id,
            doc_id=doc_id,
            text=text,
            chunk_index=0,
            token_count=len(text.split()),
            start_char=0,
            end_char=len(text),
        ),
        score=1.0,
        rank=1,
        retrieval_method="gold_premise",
    )


def evaluate_verifier_on_gold(
    gold_path: str,
    *,
    method: str = "nli",
    config: Optional[EvaluatorConfig] = None,
) -> Dict[str, Any]:
    payload = load_verifier_eval(gold_path)
    items: List[Dict[str, Any]] = payload["items"]
    cfg = config or EvaluatorConfig(method=method, allow_heuristic_fallback=False)
    cfg.method = method
    verifier = NLIVerifier(cfg)

    y_true: List[VerificationLabel] = []
    y_pred: List[VerificationLabel] = []
    rows: List[Dict[str, Any]] = []

    for i, item in enumerate(items, start=1):
        gold = parse_verification_label(item["gold_label"])
        claim = AtomicClaim(
            claim_id=item["id"],
            text=item["claim"],
            raw_sentence=item["claim"],
            cited_chunk_ids=[],
            is_abstention=(gold == VerificationLabel.AMBIGUOUS and item.get("is_abstention", False)),
        )
        if item.get("is_abstention"):
            claim.is_abstention = True
        chunk = _premise_chunk(item, i)
        pred = verifier.verify_claim(claim, [chunk])
        y_true.append(gold)
        y_pred.append(pred.label)
        rows.append(
            {
                "id": item["id"],
                "claim": item["claim"],
                "gold": gold.value,
                "pred": pred.label.value,
                "correct": gold == pred.label,
                "entailment_prob": pred.entailment_prob,
                "contradiction_prob": pred.contradiction_prob,
                "verifier_method": pred.verifier_method,
                "explanation": pred.explanation,
            }
        )

    scores = per_class_scores(y_true, y_pred)
    matrix = confusion_matrix(y_true, y_pred)
    failures = [row for row in rows if not row["correct"]]
    return {
        "gold_path": os.path.abspath(gold_path),
        "dataset_id": payload.get("dataset_id", "verifier_eval_v1"),
        "schema_version": payload.get("schema_version"),
        "annotator": payload.get("annotator"),
        "method": method,
        "n": len(items),
        "accuracy": accuracy(y_true, y_pred),
        "macro_f1": macro_f1(scores),
        "per_class": scores,
        "labels": [label.value for label in EVAL_LABEL_ORDER],
        "confusion_matrix": matrix,
        "failures": failures,
        "predictions": rows,
    }


def format_report(result: Dict[str, Any]) -> str:
    labels = result["labels"]
    matrix = result["confusion_matrix"]
    header = "gold\\pred | " + " | ".join(labels)
    rows = [header, "--- | " + " | ".join("---" for _ in labels)]
    for gold, counts in zip(labels, matrix):
        rows.append(gold + " | " + " | ".join(str(c) for c in counts))
    class_lines = [
        f"| {name} | {s['precision']:.3f} | {s['recall']:.3f} | {s['f1']:.3f} | {int(s['support'])} |"
        for name, s in result["per_class"].items()
    ]
    fail_lines = [
        f"- `{f['id']}` gold={f['gold']} pred={f['pred']}: {f['claim']}"
        for f in result["failures"]
    ] or ["- none"]
    return f"""# Verifier evaluation — {result['dataset_id']}

**Method:** `{result['method']}`  
**n:** {result['n']}  
**Accuracy:** {result['accuracy']:.4f}  
**Macro-F1:** {result['macro_f1']:.4f}  
**Annotator:** {result.get('annotator')}  
**Gold file:** `{result['gold_path']}`

Primary metrics are context-bounded: each item supplies one premise passage. This is not a world-knowledge fact check.

## Per-class scores

| Label | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(class_lines)}

## Confusion matrix (rows = gold)

{chr(10).join(rows)}

## Failures ({len(result['failures'])})

{chr(10).join(fail_lines)}

Do not treat these numbers as confirmatory RQ2 results beyond this labeled set.
"""


def write_report(result: Dict[str, Any], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    text = format_report(result)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    json_path = os.path.splitext(output_path)[0] + ".json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    return output_path
