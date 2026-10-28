"""HotpotQA multi-hop benchmark dataset importer."""

from __future__ import annotations
from typing import List, Dict, Any
from rageval.core.schemas import BenchmarkItem, GoldEvidence, GoldClaim, TestType, VerificationLabel


class HotpotQAImporter:
    """Imports and converts multi-hop HotpotQA records into RAGeval schema."""

    @staticmethod
    def normalize_record(raw: Dict[str, Any]) -> BenchmarkItem:
        qid = raw.get("_id") or f"hp_{raw.get('id', 'item')}"
        question = raw.get("question") or ""
        answer = raw.get("answer") or ""
        supporting_facts = raw.get("supporting_facts") or []

        evidence_spans = []
        gold_doc_ids = []
        for fact in supporting_facts:
            title = fact[0] if isinstance(fact, (list, tuple)) and len(fact) > 0 else "doc"
            doc_id = f"wiki_{title.replace(' ', '_')}"
            gold_doc_ids.append(doc_id)
            evidence_spans.append(GoldEvidence(doc_id=doc_id, span=title))

        gold_claims = [GoldClaim(claim=answer, status=VerificationLabel.SUPPORTED, gold_doc_ids=gold_doc_ids)] if answer else []

        return BenchmarkItem(
            id=qid,
            domain="multi_hop_knowledge",
            question=question,
            gold_answer=answer,
            gold_evidence_spans=evidence_spans,
            gold_atomic_claims=gold_claims,
            test_type=TestType.STANDARD,
            expected_abstention=False,
            metadata={"source": "HotpotQA", "level": raw.get("level", "medium")},
        )

    @classmethod
    def load_records(cls, raw_list: List[Dict[str, Any]]) -> List[BenchmarkItem]:
        return [cls.normalize_record(r) for r in raw_list]
