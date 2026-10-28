"""Unit tests for dataset benchmark importers: FinanceBench, PubMedQA, and HotpotQA."""

from rageval.dataset.importers import FinanceBenchImporter, PubMedQAImporter, HotpotQAImporter


def test_financebench_importer():
    raw_fb = [{
        "financebench_id": "fb_sample_01",
        "question": "What is the net debt of 3M in fiscal 2022?",
        "answer": "Net debt was $12.1 billion.",
        "evidence_text": "Total debt as of December 31, 2022 was $14.5 billion, with cash of $2.4 billion.",
        "doc_name": "3m_2022_10k",
        "company": "3M",
    }]
    items = FinanceBenchImporter.load_records(raw_fb)
    assert len(items) == 1
    assert items[0].id == "fb_sample_01"
    assert items[0].domain == "finance"
    assert len(items[0].gold_evidence_spans) == 1


def test_pubmedqa_importer():
    raw_pubmed = {
        "12345": {
            "QUESTION": "Is pembrolizumab effective in advanced melanoma?",
            "CONTEXTS": ["In a randomized phase 3 trial, pembrolizumab prolonged overall survival."],
            "LONG_ANSWER": "Pembrolizumab showed significant clinical benefit and improved overall survival.",
            "final_decision": "yes",
        }
    }
    items = PubMedQAImporter.load_records(raw_pubmed)
    assert len(items) == 1
    assert items[0].id == "pmqa_12345"
    assert items[0].domain == "biomedical"
    assert len(items[0].gold_atomic_claims) == 1


def test_hotpotqa_importer():
    raw_hotpot = [{
        "_id": "hp_sample_01",
        "question": "Were Arthur's Magazine and First for Women founded in the same century?",
        "answer": "yes",
        "supporting_facts": [["Arthur's Magazine", 0], ["First for Women", 0]],
    }]
    items = HotpotQAImporter.load_records(raw_hotpot)
    assert len(items) == 1
    assert items[0].id == "hp_sample_01"
    assert items[0].domain == "multi_hop_knowledge"
    assert len(items[0].gold_evidence_spans) == 2
