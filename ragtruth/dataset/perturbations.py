"""Adversarial perturbation engine for generating controlled synthetic hallucinations,

contradictions, and unanswerable queries from source corpora.
"""

from __future__ import annotations
import re
import random
from typing import List, Dict, Optional, Tuple
from ragtruth.core.schemas import Document, BenchmarkItem, TestType, GoldEvidence, GoldClaim, VerificationLabel


class PerturbationEngine:
    """Generates synthetic adversarial variants of documents and claims:

    1. Numerical & entity contradictions (e.g. reversing numbers, changing percentages).
    2. Extrapolative hallucinations (injecting plausibly phrased but unsupported propositions).
    3. Adversarial unanswerable queries with high lexical overlap.
    """

    NUMERICAL_REPLACEMENTS = {
        r"\b(\d+)%\b": lambda m: f"{max(1, (int(m.group(1)) + random.choice([15, 25, -20])))}%",
        r"\$(\d+(?:\.\d+)?)\s*billion\b": lambda m: f"${float(m.group(1)) * random.choice([0.4, 2.5]):.2f} billion",
        r"\$(\d+(?:\.\d+)?)\s*million\b": lambda m: f"${float(m.group(1)) * random.choice([0.3, 3.0]):.1f} million",
        r"\b(\d+(?:\.\d+)?)\s*ms\b": lambda m: f"{float(m.group(1)) * random.choice([5.0, 10.0]):.1f} ms",
        r"\b(\d+(?:\.\d+)?)\s*months\b": lambda m: f"{float(m.group(1)) * random.choice([0.25, 3.5]):.1f} months",
    }

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

    @classmethod
    def mutate_into_contradiction(cls, text: str) -> str:
        """Applies polarity inversion or numerical mutation to create a direct factual contradiction."""
        mutated = text

        # 1. Try phrase inversion
        for orig, inverted in cls.CONTRADICTION_PHRASES:
            if re.search(rf"\b{orig}\b", mutated, flags=re.IGNORECASE):
                mutated = re.sub(rf"\b{orig}\b", inverted, mutated, count=1, flags=re.IGNORECASE)
                return mutated

        # 2. Try numerical mutations
        for pattern, repl in cls.NUMERICAL_REPLACEMENTS.items():
            if re.search(pattern, mutated):
                mutated = re.sub(pattern, repl, mutated, count=1)
                return mutated

        # 3. Fallback: prepend explicit refutation clause
        return f"Contrary to published records, {mutated.lower()}"

    @classmethod
    def inject_hallucination(cls, answer: str) -> str:
        """Appends an unsupported factual claim to an answer to test hallucination sensitivity."""
        hallucination = random.choice(cls.HALLUCINATION_TEMPLATES)
        return f"{answer.strip()} {hallucination}"

    @classmethod
    def generate_adversarial_items_from_corpus(
        cls,
        documents: List[Document],
        count: int = 4,
    ) -> List[BenchmarkItem]:
        """Generates synthetic adversarial test items from existing documents."""
        adversarial_items: List[BenchmarkItem] = []

        for i, doc in enumerate(documents[:count]):
            # Create an unanswerable query using keywords from the document
            words = [w for w in re.findall(r"\b[A-Za-z]{4,}\b", doc.text) if w.lower() not in ("with", "from", "that", "this", "have", "were", "been")]
            sampled_terms = random.sample(words, min(3, len(words)))
            unans_question = f"What was the specific 2028 target projection for {' and '.join(sampled_terms)} mentioned in {doc.title or 'the report'}?"

            item = BenchmarkItem(
                id=f"adv_synth_unans_{i+1}",
                domain=doc.domain or "general",
                question=unans_question,
                gold_answer=None,
                gold_evidence_spans=[],
                gold_atomic_claims=[],
                test_type=TestType.UNANSWERABLE,
                expected_abstention=True,
                metadata={"synthetic": True, "source_doc_id": doc.id},
            )
            adversarial_items.append(item)

        return adversarial_items
