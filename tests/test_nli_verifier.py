"""Unit tests for NLI entailment, contradiction, and neutral classification."""

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytestmark = pytest.mark.hf

from rageval.core.schemas import AtomicClaim, Chunk, RetrievedChunk, VerificationLabel
from rageval.evaluator.nli_verifier import NLIVerifier


def test_nli_verification_entailed_and_contradiction():
    verifier = NLIVerifier()
    premise_chunk = RetrievedChunk(
        chunk=Chunk(
            id="c_fin",
            doc_id="d_fin",
            text="ApexCloud non-GAAP gross margin expanded by 180 basis points to 78.2% in Q3 2024.",
            chunk_index=0,
            token_count=15,
            start_char=0,
            end_char=80,
        ),
        score=0.95,
        rank=1,
    )

    # 1. Entailed claim
    claim_entailed = AtomicClaim(
        claim_id="c1",
        text="ApexCloud gross margin reached 78.2% in Q3 2024",
        raw_sentence="ApexCloud gross margin reached 78.2% in Q3 2024 [1].",
        cited_chunk_ids=["c_fin"],
    )
    v_ent = verifier.verify_claim(claim_entailed, [premise_chunk])
    assert v_ent.label == VerificationLabel.SUPPORTED

    # 2. Contradictory claim
    claim_contra = AtomicClaim(
        claim_id="c2",
        text="ApexCloud gross margin crashed to 12.4% in Q3 2024",
        raw_sentence="ApexCloud gross margin crashed to 12.4% in Q3 2024 [1].",
        cited_chunk_ids=["c_fin"],
    )
    v_contra = verifier.verify_claim(claim_contra, [premise_chunk])
    assert v_contra.label == VerificationLabel.CONTRADICTED

    # 3. Unsupported (Neutral) claim
    claim_neutral = AtomicClaim(
        claim_id="c3",
        text="ApexCloud partnered with NVIDIA to design autonomous quantum satellites",
        raw_sentence="ApexCloud partnered with NVIDIA to design autonomous quantum satellites.",
        cited_chunk_ids=["c_fin"],
    )
    v_neu = verifier.verify_claim(claim_neutral, [premise_chunk])
    assert v_neu.label == VerificationLabel.UNSUPPORTED
