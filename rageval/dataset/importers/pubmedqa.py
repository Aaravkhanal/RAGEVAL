"""PubMedQA biomedical clinical QA dataset importer."""

from __future__ import annotations
from typing import List, Dict, Any
from rageval.core.schemas import BenchmarkItem, GoldEvidence, GoldClaim, TestType, VerificationLabel


class PubMedQAImporter:
    """Imports and converts PubMedQA abstracts and questions into RAGeval schema."""

    @staticmethod
    def normalize_record(pmid: str, raw: Dict[str, Any]) -> BenchmarkItem:
        question = raw.get("QUESTION") or raw.get("question") or ""
        contexts = raw.get("CONTEXTS") or raw.get("context") or []
        context_str = " ".join(contexts) if isinstance(contexts, list) else str(contexts)
        long_answer = raw.get("LONG_ANSWER") or raw.get("long_answer") or raw.get("final_decision", "")

        doc_id = f"pubmed_{pmid}"
        evidence_spans = [GoldEvidence(doc_id=doc_id, span=context_str[:250])] if context_str else []

        gold_claims = []
        if long_answer:
            gold_claims.append(
                GoldClaim(claim=long_answer, status=VerificationLabel.SUPPORTED, gold_doc_ids=[doc_id])
            )

        return BenchmarkItem(
            id=f"pmqa_{pmid}",
            domain="biomedical",
            question=question,
            gold_answer=long_answer,
            gold_evidence_spans=evidence_spans,
            gold_atomic_claims=gold_claims,
            test_type=TestType.STANDARD,
            expected_abstention=False,
            metadata={"source": "PubMedQA", "pmid": pmid},
        )

    @classmethod
    def load_records(cls, data_dict: Dict[str, Any]) -> List[BenchmarkItem]:
        items = []
        for pmid, content in data_dict.items():
            items.append(cls.normalize_record(pmid, content))
        return items
