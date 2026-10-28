"""FinanceBench SEC 10-K benchmark importer and normalizer."""

from __future__ import annotations
from typing import List, Dict, Any
from rageval.core.schemas import BenchmarkItem, GoldEvidence, GoldClaim, TestType, VerificationLabel


class FinanceBenchImporter:
    """Imports and normalizes FinanceBench dataset entries into standard RAGeval schema."""

    @staticmethod
    def normalize_record(raw: Dict[str, Any], record_idx: int = 1) -> BenchmarkItem:
        qid = raw.get("financebench_id") or f"fb_{record_idx}"
        question = raw.get("question") or ""
        gold_answer = raw.get("answer") or ""
        evidence_text = raw.get("evidence_text") or raw.get("context") or ""
        doc_name = raw.get("doc_name") or "sec_10k_filing"

        evidence_spans = []
        if evidence_text:
            evidence_spans.append(
                GoldEvidence(doc_id=doc_name, span=evidence_text[:200])
            )

        # Decompose gold answer into primary gold claim
        gold_claims = []
        if gold_answer:
            gold_claims.append(
                GoldClaim(claim=gold_answer, status=VerificationLabel.SUPPORTED, gold_doc_ids=[doc_name])
            )

        return BenchmarkItem(
            id=qid,
            domain="finance",
            question=question,
            gold_answer=gold_answer,
            gold_evidence_spans=evidence_spans,
            gold_atomic_claims=gold_claims,
            test_type=TestType.STANDARD,
            expected_abstention=False,
            metadata={"source": "FinanceBench", "company": raw.get("company", "")},
        )

    @classmethod
    def load_records(cls, raw_records: List[Dict[str, Any]]) -> List[BenchmarkItem]:
        return [cls.normalize_record(r, i + 1) for i, r in enumerate(raw_records)]
