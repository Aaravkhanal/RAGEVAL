"""PyTorch Natural Language Inference (NLI) Verifier for Claim-Level Evidence Attribution."""

from __future__ import annotations
import re
from typing import List, Tuple, Dict, Optional
from rageval.core.schemas import (
    AtomicClaim,
    RetrievedChunk,
    ClaimVerification,
    VerificationLabel,
)
from rageval.core.config import EvaluatorConfig
from rageval.evaluator.label_decision import (
    ENTAIL_THRESHOLD,
    decide_claim_label,
    schema_version,
)


class NLIVerifier:
    """Evaluates factual entailment, contradiction, and neutrality (unsupported)

    between retrieved context chunks (premise) and atomic claims (hypothesis).
    """

    def __init__(self, config: Optional[EvaluatorConfig] = None):
        self.config = config or EvaluatorConfig()
        self.model_name = self.config.nli_model_name
        self.tokenizer = None
        self.model = None
        self._id2label = {}
        self.method = (self.config.method or "nli").lower()
        if self.method not in {"nli", "heuristic"}:
            raise ValueError(f"Unknown evaluator method {self.method!r}. Use 'nli' or 'heuristic'.")
        self.device = "cpu" if self.method == "heuristic" else self._resolve_device(self.config.device)
        self._load_model()

    def _resolve_device(self, req_device: str) -> str:
        import torch

        if req_device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        return req_device

    def _load_model(self) -> None:
        if self.method == "heuristic":
            self.model = None
            self.tokenizer = None
            return
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            self._id2label = {i: str(label).lower() for i, label in self.model.config.id2label.items()}
        except Exception as e:
            if self.config.allow_heuristic_fallback:
                print(
                    f"[NLIVerifier] Warning: Could not load HuggingFace model '{self.model_name}' ({e}). "
                    "Using heuristic verifier because allow_heuristic_fallback=True."
                )
                self.model = None
                self.tokenizer = None
                return
            raise RuntimeError(
                f"Failed to load NLI model '{self.model_name}'. Refusing to silently substitute a heuristic. "
                "Set evaluator.method='heuristic' or allow_heuristic_fallback=True if that is intended. "
                f"Original error: {e}"
            ) from e

    def _predict_nli_batch(self, premise_hypothesis_pairs: List[Tuple[str, str]]) -> List[Dict[str, float]]:
        """Computes probabilities: {'entailment': p_ent, 'neutral': p_neu, 'contradiction': p_con}."""
        if not premise_hypothesis_pairs:
            return []

        if self.model is not None and self.tokenizer is not None:
            return self._predict_transformer(premise_hypothesis_pairs)
        else:
            return self._heuristic_nli_batch(premise_hypothesis_pairs)

    def _predict_transformer(self, pairs: List[Tuple[str, str]]) -> List[Dict[str, float]]:
        import torch

        results = []
        batch_size = self.config.batch_size

        for i in range(0, len(pairs), batch_size):
            batch = pairs[i : i + batch_size]
            premises = [p[0] for p in batch]
            hypotheses = [p[1] for p in batch]

            inputs = self.tokenizer(
                premises,
                hypotheses,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()

            for prob in probs:
                prob_dict = {"entailment": 0.0, "neutral": 0.0, "contradiction": 0.0}
                for idx, val in enumerate(prob):
                    label_str = self._id2label.get(idx, "").lower()
                    if "entail" in label_str:
                        prob_dict["entailment"] = float(val)
                    elif "contra" in label_str:
                        prob_dict["contradiction"] = float(val)
                    else:
                        prob_dict["neutral"] = float(val)
                results.append(prob_dict)

        return results

    def _heuristic_nli_batch(self, pairs: List[Tuple[str, str]]) -> List[Dict[str, float]]:
        """Lightweight semantic heuristic for fast local testing and fallback."""
        results = []
        for premise, hypothesis in pairs:
            p_words = set(re.findall(r"\w+", premise.lower()))
            h_words = set(re.findall(r"\w+", hypothesis.lower()))
            
            # Key entity/number overlap
            h_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", hypothesis))
            p_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", premise))
            
            # Check for direct numerical conflict
            num_conflict = False
            if h_numbers and p_numbers:
                # If hypothesis asserts numbers that don't appear in premise when sharing topic words
                topic_words = h_words - set(["the", "and", "is", "was", "in", "of", "to", "for", "with", "at", "by", "a", "an"])
                if len(topic_words & p_words) >= 2 and not (h_numbers & p_numbers):
                    num_conflict = True

            intersection = h_words & p_words
            overlap_ratio = len(intersection) / max(len(h_words), 1)

            if num_conflict or "contrary" in hypothesis.lower() or "discontinued" in hypothesis.lower():
                results.append({"entailment": 0.05, "neutral": 0.15, "contradiction": 0.80})
            elif overlap_ratio >= 0.55:
                results.append({"entailment": 0.85, "neutral": 0.10, "contradiction": 0.05})
            elif overlap_ratio >= 0.30:
                results.append({"entailment": 0.20, "neutral": 0.70, "contradiction": 0.10})
            else:
                results.append({"entailment": 0.05, "neutral": 0.85, "contradiction": 0.10})

        return results

    def verify_claim(
        self,
        claim: AtomicClaim,
        retrieved_chunks: List[RetrievedChunk],
    ) -> ClaimVerification:
        """Verifies an individual atomic claim against candidate chunks.

        Tests all retrieved chunks so faithfulness is independent of citation attribution.
        """
        # If the claim is an abstention statement
        if claim.is_abstention or any(
            term in claim.text.lower()
            for term in ["do not have sufficient information", "cannot be answered", "insufficient context"]
        ):
            return ClaimVerification(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                label=VerificationLabel.AMBIGUOUS,
                confidence=None,
                entailment_prob=0.0,
                neutral_prob=1.0,
                contradiction_prob=0.0,
                explanation="Abstention statement; excluded from claim-support denominators.",
                verifier_method=self.method,
                label_schema_version=schema_version(),
            )

        if not retrieved_chunks:
            return ClaimVerification(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                label=VerificationLabel.UNSUPPORTED,
                confidence=1.0,
                entailment_prob=0.0,
                neutral_prob=1.0,
                contradiction_prob=0.0,
                explanation="No context chunks available to support claim.",
                verifier_method=self.method,
                label_schema_version=schema_version(),
            )

        # Faithfulness considers the whole retrieved pool. The citation audit checks
        # separately whether the specific cited chunks support the claim.
        candidate_chunks = retrieved_chunks

        # Evaluate pairs
        pairs = [(c.chunk.text, claim.text) for c in candidate_chunks]
        nli_outputs = self._predict_nli_batch(pairs)

        best_entailment_score = 0.0
        best_contradiction_score = 0.0
        best_entail_chunk_id = None
        best_entail_chunk_text = None
        best_contra_chunk_id = None
        best_contra_chunk_text = None

        supporting_ids = []
        contradicting_ids = []

        for c, scores in zip(candidate_chunks, nli_outputs):
            p_ent = scores["entailment"]
            p_con = scores["contradiction"]

            if p_ent > ENTAIL_THRESHOLD:
                supporting_ids.append(c.chunk.id)
            if p_con > ENTAIL_THRESHOLD:
                contradicting_ids.append(c.chunk.id)

            if p_ent > best_entailment_score:
                best_entailment_score = p_ent
                best_entail_chunk_id = c.chunk.id
                best_entail_chunk_text = c.chunk.text

            if p_con > best_contradiction_score:
                best_contradiction_score = p_con
                best_contra_chunk_id = c.chunk.id
                best_contra_chunk_text = c.chunk.text

        label, explanation = decide_claim_label(
            best_entailment_score,
            best_contradiction_score,
            len(supporting_ids),
            len(contradicting_ids),
        )
        if label == VerificationLabel.CONTRADICTED:
            confidence = best_contradiction_score
            best_chunk_id = best_contra_chunk_id or best_entail_chunk_id
            best_chunk_text = best_contra_chunk_text or best_entail_chunk_text
        elif label in (VerificationLabel.SUPPORTED, VerificationLabel.PARTIALLY_SUPPORTED):
            confidence = best_entailment_score
            best_chunk_id = best_entail_chunk_id or best_contra_chunk_id
            best_chunk_text = best_entail_chunk_text or best_contra_chunk_text
        else:
            confidence = 1.0 - max(best_entailment_score, best_contradiction_score)
            best_chunk_id = best_entail_chunk_id or best_contra_chunk_id
            best_chunk_text = best_entail_chunk_text or best_contra_chunk_text

        span_start = None
        span_end = None
        exact_span_text = None

        if best_chunk_id and label in (
            VerificationLabel.SUPPORTED,
            VerificationLabel.CONTRADICTED,
            VerificationLabel.PARTIALLY_SUPPORTED,
        ):
            from rageval.evaluator.span_localizer import SpanLocalizer
            matching_chunk_obj = next((r.chunk for r in candidate_chunks if r.chunk.id == best_chunk_id), None)
            if matching_chunk_obj:
                span_match = SpanLocalizer.find_best_evidence_span(
                    claim_text=claim.text,
                    chunk=matching_chunk_obj,
                    is_supporting=(label != VerificationLabel.CONTRADICTED),
                )
                if span_match:
                    span_start = span_match.start_char
                    span_end = span_match.end_char
                    exact_span_text = span_match.exact_span

        method_id = self.method if self.model is not None else "heuristic"
        return ClaimVerification(
            claim_id=claim.claim_id,
            claim_text=claim.text,
            label=label,
            confidence=confidence,
            entailment_prob=best_entailment_score,
            neutral_prob=max(0.0, 1.0 - max(best_entailment_score, best_contradiction_score)),
            contradiction_prob=best_contradiction_score,
            supporting_chunk_ids=supporting_ids,
            contradicting_chunk_ids=contradicting_ids,
            best_matching_chunk_id=best_chunk_id,
            best_matching_chunk_text=best_chunk_text,
            evidence_span_start=span_start,
            evidence_span_end=span_end,
            evidence_exact_text=exact_span_text,
            explanation=explanation,
            verifier_method=method_id,
            label_schema_version=schema_version(),
        )
