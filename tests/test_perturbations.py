"""Unit tests for adversarial perturbation mutations."""

from ragtruth.core.schemas import Document
from ragtruth.dataset.perturbations import PerturbationEngine


def test_perturbation_contradiction_and_hallucination():
    text = "ApexCloud non-GAAP gross margin increased to 78.2%."
    contradiction = PerturbationEngine.mutate_into_contradiction(text)
    assert contradiction != text
    assert "sharply contracted" in contradiction or "%" in contradiction

    answer = "The platform processed queries with 1.4 ms latency."
    hallucinated = PerturbationEngine.inject_hallucination(answer)
    assert len(hallucinated) > len(answer)
    assert answer in hallucinated


def test_synthetic_unanswerable_generation():
    doc = Document(
        id="d_test",
        title="Distributed Sharding Protocol",
        text="Consistent hashing distributes shard keys across planetary regions with monotonic leases.",
    )
    items = PerturbationEngine.generate_adversarial_items_from_corpus([doc], count=1)
    assert len(items) == 1
    assert items[0].expected_abstention is True
    assert items[0].test_type.value == "unanswerable"
