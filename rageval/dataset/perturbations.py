"""Adversarial perturbation engine for generating controlled synthetic hallucinations,

contradictions, and unanswerable queries from source corpora.
"""

from __future__ import annotations

import random
import re
from typing import List, Optional, Tuple

from rageval.analysis.failure_taxonomy import tag_synthetic_item
from rageval.core.schemas import BenchmarkItem, Document, TestType


class PerturbationEngine:
    """Generates synthetic adversarial variants of documents and claims:

    1. Numerical & entity contradictions (e.g. reversing numbers, changing percentages).
    2. Extrapolative hallucinations (injecting plausibly phrased but unsupported propositions).
    3. Adversarial unanswerable queries with high lexical overlap.

    All stochastic choices go through `random.Random(seed)` so the same seed
    yields the same mutation.
    """

    CONTRADICTION_PHRASES = [
        ("increased", "sharply contracted"),
        ("expanded", "diminished"),
        ("exceeded", "fell critically below"),
        ("improved", "deteriorated"),
        ("guarantees", "completely fails to ensure"),
        ("launched", "indefinitely canceled"),
        ("without safety drivers", "requiring mandatory human intervention"),
    ]

    HALLUCINATION_TEMPLATES = [
        "In addition, independent audits by ISO-27001 verified compliance across all international regions.",
        "Furthermore, management announced a strategic multi-year joint venture with QuantumAI Inc.",
        "Crucially, secondary endpoints revealed unexpected efficacy in treating pediatric neurological trauma.",
        "Historical telemetry confirmed zero unplanned outages during the preceding four fiscal cycles.",
    ]

    @staticmethod
    def _rng(seed: Optional[int]) -> random.Random:
        return random.Random(seed)

    @classmethod
    def _numerical_replacements(cls, rng: random.Random) -> dict:
        return {
            r"\b(\d+(?:\.\d+)?)%": lambda m: f"{max(1, (int(float(m.group(1))) + rng.choice([15, 25, -20])))}%",
            r"\$(\d+(?:\.\d+)?)\s*billion\b": lambda m: f"${float(m.group(1)) * rng.choice([0.4, 2.5]):.2f} billion",
            r"\$(\d+(?:\.\d+)?)\s*million\b": lambda m: f"${float(m.group(1)) * rng.choice([0.3, 3.0]):.1f} million",
            r"\b(\d+(?:\.\d+)?)\s*ms\b": lambda m: f"{float(m.group(1)) * rng.choice([5.0, 10.0]):.1f} ms",
            r"\b(\d+(?:\.\d+)?)\s*months\b": lambda m: f"{float(m.group(1)) * rng.choice([0.25, 3.5]):.1f} months",
        }

    @classmethod
    def mutate_into_contradiction(cls, text: str, seed: Optional[int] = None) -> str:
        """Applies polarity inversion or numerical mutation to create a direct factual contradiction."""
        rng = cls._rng(seed)
        mutated = text

        for orig, inverted in cls.CONTRADICTION_PHRASES:
            if re.search(rf"\b{orig}\b", mutated, flags=re.IGNORECASE):
                mutated = re.sub(rf"\b{orig}\b", inverted, mutated, count=1, flags=re.IGNORECASE)
                return mutated

        for pattern, repl in cls._numerical_replacements(rng).items():
            if re.search(pattern, mutated):
                mutated = re.sub(pattern, repl, mutated, count=1)
                return mutated

        return f"Contrary to published records, {mutated.lower()}"

    @classmethod
    def inject_hallucination(cls, answer: str, seed: Optional[int] = None) -> str:
        """Appends an unsupported factual claim to an answer to test hallucination sensitivity."""
        rng = cls._rng(seed)
        hallucination = rng.choice(cls.HALLUCINATION_TEMPLATES)
        return f"{answer.strip()} {hallucination}"

    @classmethod
    def make_conflict_pair(
        cls,
        control: BenchmarkItem,
        source_span: str,
        *,
        seed: int = 0,
        conflict_doc_id: str = "doc_conflict_synth",
        item_id: Optional[str] = None,
    ) -> Tuple[Document, BenchmarkItem]:
        """Same question as `control`, plus a document that contradicts `source_span`."""
        mutated = cls.mutate_into_contradiction(source_span, seed=seed)
        doc = Document(
            id=conflict_doc_id,
            title="Synthetic conflict document",
            text=mutated,
            domain=control.domain,
            license="original-synthetic-in-repo",
            provenance="PerturbationEngine.make_conflict_pair",
            metadata=tag_synthetic_item("conflict_pair"),
        )
        pair_id = control.pair_id or control.id
        item = BenchmarkItem(
            id=item_id or f"{control.id}_with_conflict",
            domain=control.domain,
            question=control.question,
            gold_answer=(
                "Sources conflict. The control document and the added document disagree "
                f"on the same proposition. Control span: {source_span} Added span: {mutated}"
            ),
            gold_evidence_spans=list(control.gold_evidence_spans),
            gold_atomic_claims=list(control.gold_atomic_claims),
            test_type=TestType.CONFLICTING,
            expected_abstention=False,
            answerability="answerable",
            scenario_type="conflicting",
            split=control.split,
            pair_id=pair_id,
            pair_role="with_conflict",
            reviewed=False,
            metadata={
                **tag_synthetic_item("conflict_pair"),
                "pair_id": pair_id,
                "pair_role": "with_conflict",
                "conflict_docs": [conflict_doc_id],
                "control_item_id": control.id,
            },
        )
        return doc, item

    @classmethod
    def generate_adversarial_items_from_corpus(
        cls,
        documents: List[Document],
        count: int = 4,
        seed: Optional[int] = None,
    ) -> List[BenchmarkItem]:
        """Generates synthetic adversarial test items from existing documents."""
        rng = cls._rng(seed)
        adversarial_items: List[BenchmarkItem] = []

        for i, doc in enumerate(documents[:count]):
            words = [
                w
                for w in re.findall(r"\b[A-Za-z]{4,}\b", doc.text)
                if w.lower() not in ("with", "from", "that", "this", "have", "were", "been")
            ]
            k = min(3, len(words))
            sampled_terms = rng.sample(words, k) if k else ["topic"]
            unans_question = (
                f"What was the specific 2028 target projection for "
                f"{' and '.join(sampled_terms)} mentioned in {doc.title or 'the report'}?"
            )
            meta = tag_synthetic_item("unanswerable")
            meta["source_doc_id"] = doc.id
            item = BenchmarkItem(
                id=f"adv_synth_unans_{i+1}",
                domain=doc.domain or "general",
                question=unans_question,
                gold_answer=None,
                gold_evidence_spans=[],
                gold_atomic_claims=[],
                test_type=TestType.UNANSWERABLE,
                expected_abstention=True,
                answerability="unanswerable",
                scenario_type="unanswerable",
                reviewed=False,
                metadata=meta,
            )
            adversarial_items.append(item)

        return adversarial_items
