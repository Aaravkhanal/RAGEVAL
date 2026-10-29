"""External RAG adapter: question + chunks + answer in, scores out. Fast path is heuristic."""

import json

from rageval.integrations.external import (
    SCHEMA,
    score_answer,
    score_file,
    score_records,
)


def test_example_jsonl_scores():
    from rageval.integrations.external import iter_score_records, score_records

    results = score_records(
        iter_score_records("configs/examples/external_score.jsonl"),
        method="heuristic",
    )
    assert len(results) == 2
    assert results[0].faithfulness_score == 1.0
    assert results[1].faithfulness_score < 1.0


def test_score_answer_supported_heuristic():
    result = score_answer(
        "What was the margin?",
        "Gross margin was 78.2% [1].",
        ["ApexCloud reported that gross margin reached 78.2% in Q3 2024."],
        method="heuristic",
        query_id="ext_001",
    )
    assert result.query_id == "ext_001"
    assert result.faithfulness_score == 1.0
    assert result.verifications
    assert result.verifications[0].verifier_method == "heuristic"


def test_score_answer_unsupported_heuristic():
    result = score_answer(
        "Where is HQ?",
        "Headquarters moved to an offshore volcanic island.",
        ["ApexCloud reported regular quarterly financials in Delaware."],
        method="heuristic",
        query_id="ext_002",
    )
    assert result.faithfulness_score < 1.0
    assert result.hallucination_rate > 0.0


def test_score_jsonl_roundtrip(tmp_path):
    src = tmp_path / "in.jsonl"
    src.write_text(
        json.dumps(
            {
                "id": "a1",
                "question": "What is the test question?",
                "answer": "The test is valid [1].",
                "contexts": ["The test is valid."],
            }
        )
        + "\n"
        + json.dumps(
            {
                "query_id": "a2",
                "question": "What is missing?",
                "answer": "The corpus lists a secret code 999.",
                "context": "The test is valid.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.jsonl"
    score_file(str(src), str(out), method="heuristic")
    lines = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line]
    assert len(lines) == 2
    assert lines[0]["schema"] == SCHEMA
    assert lines[0]["query_id"] == "a1"
    assert lines[0]["faithfulness_score"] == 1.0
    assert lines[1]["query_id"] == "a2"
    assert "api_key" not in json.dumps(lines)


def test_score_json_array(tmp_path):
    src = tmp_path / "in.json"
    src.write_text(
        json.dumps(
            [
                {
                    "id": "b1",
                    "question": "Q",
                    "answer": "The test is valid.",
                    "chunks": [{"text": "The test is valid.", "doc_id": "d1"}],
                }
            ]
        ),
        encoding="utf-8",
    )
    results = score_records(
        json.loads(src.read_text(encoding="utf-8")),
        method="heuristic",
    )
    assert results[0].query_id == "b1"
    assert results[0].retrieved_chunks[0].chunk.doc_id == "d1"


def test_score_cli(tmp_path):
    import subprocess
    import sys

    src = tmp_path / "in.jsonl"
    src.write_text(
        json.dumps(
            {
                "id": "cli1",
                "question": "What is the test question?",
                "answer": "The test is valid.",
                "contexts": ["The test is valid."],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.jsonl"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "rageval.cli",
            "score",
            "--input",
            str(src),
            "--output",
            str(out),
            "--method",
            "heuristic",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert out.is_file()
    row = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert row["query_id"] == "cli1"


def test_monitor_rag_heuristic_is_fast():
    from rageval.core.config import EvaluatorConfig
    from rageval.evaluator.evaluator import RAGEvalEvaluator
    from rageval.integrations.decorator import monitor_rag

    evaluator = RAGEvalEvaluator(EvaluatorConfig(method="heuristic", allow_heuristic_fallback=False))

    @monitor_rag(evaluator=evaluator)
    def sample(query: str):
        return {
            "answer": "The test is valid [1].",
            "contexts": ["The test is valid."],
        }

    result = sample(query="What is the test question?")
    assert result["rageval_evaluation"].faithfulness_score == 1.0
