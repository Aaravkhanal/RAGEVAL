"""Unit tests for streaming token verification and guardrail triggering."""

from ragtruth.core.schemas import Chunk, RetrievedChunk
from ragtruth.server.streaming import StreamingVerificationSession


def test_streaming_session_sentence_assembly_and_guardrail():
    chunk = RetrievedChunk(
        chunk=Chunk(
            id="c1", doc_id="d1",
            text="ApexCloud reported gross margin of 78.2% in Q3 2024.",
            chunk_index=0, token_count=10, start_char=0, end_char=50,
        ),
        score=1.0, rank=1,
    )

    session = StreamingVerificationSession(
        question="What was ApexCloud gross margin?",
        retrieved_chunks=[chunk],
        hallucination_guardrail_threshold=0.40,
        fail_on_contradiction=True,
    )

    # Stream tokens for Sentence 1 (Faithful)
    tokens_sent1 = ["ApexCloud ", "reported ", "gross ", "margin ", "of ", "78.2% [1]. "]
    for tok in tokens_sent1:
        ev = session.process_token(tok)
        if ev:
            assert ev["event"] == "sentence_verified"
            assert ev["running_faithfulness"] == 1.0
            assert ev["guardrail_triggered"] is False

    # Stream tokens for Sentence 2 (Contradictory)
    tokens_sent2 = ["However, ", "gross ", "margin ", "crashed ", "to ", "12.4% [1]."]
    for tok in tokens_sent2:
        session.process_token(tok)

    final_ev = session.flush()
    assert final_ev is not None
    assert final_ev["guardrail_triggered"] is True
    assert "contradiction" in (final_ev["guardrail_alert"] or "").lower()
