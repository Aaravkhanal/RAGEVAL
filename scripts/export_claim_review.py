"""Export a blinded human-review queue from a recorded benchmark run.

Example: python scripts/export_claim_review.py --summaries reports/phase7/live_matrix_v1/summaries.json \
    --config Dense_Chunk256_Baseline --output data/gold/review/claim_review_v1.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def export_review(summaries_path: Path, config_name: str, output_path: Path) -> int:
    summaries = json.loads(summaries_path.read_text(encoding="utf-8"))
    selected = next((row for row in summaries if row["config_name"] == config_name), None)
    if selected is None:
        raise ValueError(f"Unknown configuration {config_name!r}")
    records = []
    for result in selected["results"]:
        records.append({
            "query_id": result["query_id"],
            "question": result["question"],
            "answer": result["generated_answer"],
            "retrieved_chunks": [
                {"chunk_id": row["chunk"]["id"], "text": row["chunk"]["text"]}
                for row in result["retrieved_chunks"]
            ],
            "proposed_claims": [
                {"text": claim["text"], "char_start": claim["char_start"], "char_end": claim["char_end"], "cited_chunk_ids": claim["cited_chunk_ids"]}
                for claim in result["claims"]
                if not claim["is_abstention"]
            ],
            "human_claim_spans": None,
            "human_support_labels": None,
            "human_citation_labels": None,
        })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export generated answers for independent claim review")
    parser.add_argument("--summaries", type=Path, required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(f"Exported {export_review(args.summaries, args.config, args.output)} review items")


if __name__ == "__main__":
    main()
