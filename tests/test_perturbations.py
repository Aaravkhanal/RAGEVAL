"""Unit tests for adversarial perturbation mutations."""

from rageval.core.schemas import BenchmarkItem, Document, TestType
from rageval.dataset.pairs import group_paired_items
from rageval.dataset.perturbations import PerturbationEngine


def test_perturbation_contradiction_and_hallucination():
    text = "ApexCloud non-GAAP gross margin increased to 78.2%."
    contradiction = PerturbationEngine.mutate_into_contradiction(text)
    assert contradiction != text
    assert "sharply contracted" in contradiction or "%" in contradiction

    answer = "The platform processed queries with 1.4 ms latency."
    hallucinated = PerturbationEngine.inject_hallucination(answer)
    assert len(hallucinated) > len(answer)
    assert answer in hallucinated


def test_perturbation_determinism_with_seed():
    text = "Median GET latency was 2.1 ms."
    a = PerturbationEngine.mutate_into_contradiction(text, seed=7)
    b = PerturbationEngine.mutate_into_contradiction(text, seed=7)
    assert a == b
    assert a != text
    assert any(
        PerturbationEngine.mutate_into_contradiction(text, seed=s) != a for s in range(20)
    )

    h1 = PerturbationEngine.inject_hallucination("Base claim.", seed=3)
    h2 = PerturbationEngine.inject_hallucination("Base claim.", seed=3)
    assert h1 == h2
    assert any(
        PerturbationEngine.inject_hallucination("Base claim.", seed=s) != h1 for s in range(20)
    )


def test_synthetic_unanswerable_generation():
    doc = Document(
        id="d_test",
        title="Distributed Sharding Protocol",
        text="Consistent hashing distributes shard keys across planetary regions with monotonic leases.",
    )
    items = PerturbationEngine.generate_adversarial_items_from_corpus([doc], count=1, seed=0)
    assert len(items) == 1
    assert items[0].expected_abstention is True
    assert items[0].test_type.value == "unanswerable"
    assert items[0].metadata["failure_taxonomy_tag"] == "generation"
    assert items[0].metadata["synthetic"] is True
    again = PerturbationEngine.generate_adversarial_items_from_corpus([doc], count=1, seed=0)
    assert again[0].question == items[0].question


def test_make_conflict_pair_keeps_question():
    control = BenchmarkItem(
        id="c1",
        question="What was median GET latency?",
        gold_answer="2.1 ms",
        test_type=TestType.STANDARD,
        pair_id="pair_latency",
        pair_role="control",
    )
    doc, conflict = PerturbationEngine.make_conflict_pair(
        control, "median GET latency was 2.1 ms", seed=1
    )
    assert conflict.question == control.question
    assert conflict.pair_role == "with_conflict"
    assert conflict.scenario_type == "conflicting"
    assert doc.text != "median GET latency was 2.1 ms"
    grouped = group_paired_items([control, conflict])
    assert grouped["pair_latency"].same_question() is True
    assert grouped["pair_latency"].is_complete() is True
