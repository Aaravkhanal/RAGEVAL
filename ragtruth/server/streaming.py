"""Real-time streaming claim verification and hallucination guardrail protocol."""

from __future__ import annotations
import json
import re
from typing import AsyncGenerator, List, Dict, Any, Optional
from ragtruth.core.schemas import Chunk, RetrievedChunk, VerificationLabel
from ragtruth.evaluator.decomposer import AtomicClaimDecomposer
from ragtruth.evaluator.nli_verifier import NLIVerifier


class StreamingVerificationSession:
    """Manages an active streaming response session.

    As tokens stream in, identifies sentence boundaries and verifies claims in real-time,
    triggering early-stopping guardrail alerts if unfaithful or contradictory claims are detected.
    """

    def __init__(
        self,
        question: str,
        retrieved_chunks: List[RetrievedChunk],
        verifier: Optional[NLIVerifier] = None,
        hallucination_guardrail_threshold: float = 0.50,
        fail_on_contradiction: bool = True,
    ):
        self.question = question
        self.retrieved_chunks = retrieved_chunks
        self.verifier = verifier or NLIVerifier()
        self.hallucination_threshold = hallucination_guardrail_threshold
        self.fail_on_contradiction = fail_on_contradiction

        self.buffer: str = ""
        self.verified_sentences: List[str] = []
        self.all_verifications: List[Dict[str, Any]] = []
        self.total_claims_count: int = 0
        self.entailed_count: int = 0
        self.neutral_count: int = 0
        self.contradiction_count: int = 0
        self.guardrail_triggered: bool = False

    def _extract_completed_sentence(self) -> Optional[str]:
        # Match sentence boundary: [.!?] followed by whitespace and a capital/digit, or multiple spaces
        pattern = re.compile(r'^(.*?(?:(?<=[.!?])(?<!\d\.)(?=\s+[A-Z0-9]|\s{2,})))(.*)$', re.DOTALL)
        match = pattern.match(self.buffer)
        if match:
            completed = match.group(1).strip()
            self.buffer = match.group(2).lstrip()
            return completed
        return None

    def process_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Appends token to buffer. If a full sentence is completed, evaluates it immediately."""
        self.buffer += token
        sentence = self._extract_completed_sentence()
        if sentence:
            return self._verify_sentence(sentence)
        return None

    def flush(self) -> Optional[Dict[str, Any]]:
        """Processes any remaining text in buffer upon stream close."""
        remaining = self.buffer.strip()
        self.buffer = ""
        if remaining:
            return self._verify_sentence(remaining)
        return None

    def _verify_sentence(self, sentence: str) -> Dict[str, Any]:
        self.verified_sentences.append(sentence)
        claims = AtomicClaimDecomposer.decompose(sentence, self.retrieved_chunks)

        sentence_verifications = []
        sentence_has_contradiction = False

        for claim in claims:
            v = self.verifier.verify_claim(claim, self.retrieved_chunks)
            self.total_claims_count += 1

            if v.label == VerificationLabel.ENTAILEMENT:
                self.entailed_count += 1
            elif v.label == VerificationLabel.NEUTRAL:
                self.neutral_count += 1
            elif v.label == VerificationLabel.CONTRADICTION:
                self.contradiction_count += 1
                sentence_has_contradiction = True

            v_dict = {
                "claim_id": v.claim_id,
                "claim_text": v.claim_text,
                "label": v.label.value,
                "confidence": v.confidence,
                "evidence_exact_text": v.evidence_exact_text,
                "explanation": v.explanation,
            }
            sentence_verifications.append(v_dict)
            self.all_verifications.append(v_dict)

        # Compute running faithfulness
        running_faithfulness = (
            (self.entailed_count / self.total_claims_count) if self.total_claims_count > 0 else 1.0
        )
        running_hallucination = (
            (self.neutral_count / self.total_claims_count) if self.total_claims_count > 0 else 0.0
        )

        # Guardrail check
        guardrail_alert = None
        if self.fail_on_contradiction and sentence_has_contradiction:
            self.guardrail_triggered = True
            guardrail_alert = "Critical Guardrail Triggered: Generation produced a direct factual contradiction!"
        elif running_hallucination > self.hallucination_threshold and self.total_claims_count >= 2:
            self.guardrail_triggered = True
            guardrail_alert = f"Guardrail Alert: Hallucination rate reached {running_hallucination:.1%}."

        return {
            "event": "sentence_verified",
            "sentence": sentence,
            "claims": sentence_verifications,
            "running_faithfulness": round(running_faithfulness, 4),
            "running_hallucination_rate": round(running_hallucination, 4),
            "guardrail_triggered": self.guardrail_triggered,
            "guardrail_alert": guardrail_alert,
        }
