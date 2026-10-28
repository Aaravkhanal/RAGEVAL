"""Unit tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
from rageval.server.app import app

client = TestClient(app)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "rageval"}


def test_evaluate_answer_api():
    payload = {
        "question": "What was ApexCloud gross margin?",
        "answer": "ApexCloud reached a 78.2% gross margin [1].",
        "context_chunks": [
            "ApexCloud reported that gross margin reached 78.2% in Q3 2024.",
        ],
    }
    res = client.post("/evaluate/answer", json=payload)
    assert res.status_code == 200
    data = res.json()["evaluation"]
    assert "faithfulness_score" in data
    assert data["faithfulness_score"] == 1.0
    assert len(data["claims"]) >= 1
    assert data["verifications"][0]["label"] == "supported"
