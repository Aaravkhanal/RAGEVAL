"""Frozen, source-separated public-document benchmark (single-author labels)."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from rageval.core.assets import resolve_asset
from rageval.core.labels import VerificationLabel
from rageval.core.schemas import BenchmarkItem, Document, GoldClaim, GoldEvidence, TestType
from rageval.dataset.chunk_benchmark_v1 import build_benchmark as build_dev

DATASET_ID = "benchmark_v2"
VERSION = "2.0.0"
DATE = "2026-11-02"
LICENSE = "US-government-work-public-domain-17USC105"

# Four source pages not present in benchmark_v1 or chunk_benchmark_v1.
QUESTIONS = (
    (8, "Where did Apollo 8 launch from?", "Cape Kennedy.", "Apollo 8 launched from Cape Kennedy"),
    (8, "Who were the Apollo 8 astronauts?", "Frank Borman, James Lovell Jr., and William Anders.", "Frank Borman, James Lovell Jr. and William Anders"),
    (8, "How many telecasts did Apollo 8 conduct?", "Six.", "Six telecasts were conducted during the mission"),
    (8, "How long was Apollo 8 in lunar orbit?", "20 hours.", "During the 20-hour period in lunar orbit"),
    (9, "What was Apollo 9's primary objective?", "An Earth-orbital engineering test of the first crewed lunar module.", "an Earth-orbital engineering test of the first crewed lunar module"),
    (9, "When did Apollo 9 launch?", "March 3, 1969.", "Apollo 9 launched from Kennedy Space center on March 3, 1969"),
    (9, "How many times did Apollo 9 perform CSM and LM rendezvous and docking?", "Twice.", "This was performed twice"),
    (9, "Why was Schweickart's scheduled two-hour EVA scrubbed?", "Because of nausea.", "Because of nausea, Schweickart’s scheduled two-hour EVA"),
    (10, "Did Apollo 10 land on the Moon?", "No; it rehearsed a lunar landing without landing.", "except the landing"),
    (10, "When did Apollo 10 launch?", "May 18, 1969.", "Apollo 10 launched from Cape Kennedy on May 18, 1969"),
    (10, "Which landing site did Apollo 10's lunar module fly over?", "Landing Site 2 in the Sea of Tranquility.", "Landing Site 2 in the Sea of Tranquility"),
    (10, "How many of Apollo 10's four planned midcourse corrections were needed?", "One.", "only one of four midcourse corrections was needed"),
    (17, "Where did Apollo 17 land?", "Taurus-Littrow highlands and valley.", "Taurus-Littrow highlands and valley area"),
    (17, "Who was the first scientist-astronaut to land on the Moon?", "Harrison Schmitt.", "first scientist-astronaut to land on moon: Harrison Schmitt"),
    (17, "How far did Apollo 17's lunar rover travel?", "30.5 kilometers.", "lunar rover vehicle traversed a total of 30.5 kilometers"),
    (17, "How long did Ronald Evans's transearth EVA last?", "One hour and six minutes.", "lasted one hour, six minutes"),
)

UNANSWERABLE = (
    "What was the serial number of Apollo 8's sextant?",
    "What was the personal phone number of Apollo 9's commander?",
    "How much did the Apollo 10 lunar module's paint cost?",
    "What was the Apollo 17 rover's tire pressure?",
)

CONFLICTS = (
    ("apollo10", "Apollo 10 Mission Details — altered copy", "Apollo 10 landed on the Moon at Landing Site 2 in the Sea of Tranquility. This altered statement conflicts with NASA's mission details.", "Did Apollo 10 land on the Moon?", "No; Apollo 10 did not land on the Moon.", "except the landing"),
    ("apollo17", "Apollo 17 Mission Details — altered copy", "Apollo 17's lunar rover traversed a total of 3.5 kilometers. This altered statement conflicts with NASA's mission details.", "How far did Apollo 17's lunar rover travel?", "30.5 kilometers.", "lunar rover vehicle traversed a total of 30.5 kilometers"),
)


def build_benchmark() -> tuple[list[Document], list[BenchmarkItem]]:
    dev_docs, dev_items = build_dev()
    docs = list(dev_docs)
    items = [item.model_copy(update={"id": f"v2_dev_{item.id}"}) for item in dev_items]
    for n in (8, 9, 10, 17):
        path = Path(resolve_asset(f"data/datasets/{DATASET_ID}/sources/apollo{n}.txt"))
        content = path.read_bytes()
        source = f"https://www.nasa.gov/missions/apollo/apollo-{n}-mission-details/"
        docs.append(Document(
            id=f"doc_apollo{n}", title=f"Apollo {n} Mission Details", domain="space",
            text=re.sub(r"\s+", " ", content.decode("utf-8")).strip(),
            license=LICENSE, source_url=source, retrieved_date=DATE,
            provenance=f"Pinned main-content paragraph snapshot from {source} on {DATE}.",
            metadata={"source_sha256": hashlib.sha256(content).hexdigest(), "kind": "us_gov_snapshot"},
        ))
    for source, title, content, _, _, _ in CONFLICTS:
        docs.append(Document(
            id=f"doc_{source}_altered", title=title, domain="space", text=content,
            license="synthetic-perturbation", source_url=f"synthetic://benchmark_v2/{source}_altered",
            provenance="Benchmark-authored contradiction; not a NASA document.",
            metadata={"synthetic": True, "kind": "adversarial_conflict"},
        ))
    by_id = {doc.id: doc for doc in docs}
    if len({d.source_url for d in docs}) != len(docs):
        raise ValueError("Source URLs must be unique across splits")
    for i, (n, question, answer, evidence) in enumerate(QUESTIONS, 1):
        doc_id = f"doc_apollo{n}"
        if evidence not in by_id[doc_id].text:
            raise ValueError(f"Gold evidence missing for test item {i}: {evidence}")
        items.append(BenchmarkItem(
            id=f"v2_test_{i:03d}", domain="space", question=question,
            gold_answer=answer, gold_evidence_spans=[GoldEvidence(doc_id=doc_id, span=evidence)],
            gold_atomic_claims=[GoldClaim(claim=answer, status=VerificationLabel.SUPPORTED, gold_doc_ids=[doc_id])],
            split="test", metadata={"annotation_status": "single_author_unreviewed"},
        ))
    for i, question in enumerate(UNANSWERABLE, len(QUESTIONS) + 1):
        items.append(BenchmarkItem(
            id=f"v2_test_{i:03d}", domain="space", question=question,
            gold_answer=None, test_type=TestType.UNANSWERABLE,
            expected_abstention=True, answerability="unanswerable",
            scenario_type="unanswerable", split="test",
            metadata={"annotation_status": "single_author_unreviewed"},
        ))
    for i, (source, _, _, question, answer, evidence) in enumerate(CONFLICTS, len(QUESTIONS) + len(UNANSWERABLE) + 1):
        doc_id = f"doc_{source}"
        if evidence not in by_id[doc_id].text:
            raise ValueError(f"Conflict evidence missing for {source}")
        items.append(BenchmarkItem(
            id=f"v2_test_{i:03d}", domain="space", question=question,
            gold_answer=answer, gold_evidence_spans=[GoldEvidence(doc_id=doc_id, span=evidence)],
            gold_atomic_claims=[GoldClaim(claim=answer, status=VerificationLabel.SUPPORTED, gold_doc_ids=[doc_id])],
            test_type=TestType.CONFLICTING, scenario_type="conflicting", split="test",
            metadata={"annotation_status": "single_author_unreviewed", "conflicting_doc_id": f"doc_{source}_altered"},
        ))
    return docs, items


def write_dataset(data_dir: str = "data") -> str:
    docs, items = build_benchmark()
    directory = Path(data_dir) / "datasets" / DATASET_ID
    directory.mkdir(parents=True, exist_ok=True)
    subsets = {
        "items": items,
        "items_dev": [i for i in items if i.split == "dev"],
        "items_test": [i for i in items if i.split == "test"],
        "items_standard": [i for i in items if i.test_type == TestType.STANDARD],
        "items_adversarial": [i for i in items if i.test_type != TestType.STANDARD],
        "items_independent": [],
    }
    (directory / "corpus.json").write_text(json.dumps([d.model_dump() for d in docs], indent=2) + "\n")
    for name, subset in subsets.items():
        (directory / f"{name}.json").write_text(json.dumps([i.model_dump(mode="json") for i in subset], indent=2) + "\n")
    manifest = {
        "dataset_id": DATASET_ID, "version": VERSION, "synthetic": True,
        "license": "Mixed: public-domain US government snapshots plus two synthetic perturbations",
        "documents": f"data/datasets/{DATASET_ID}/corpus.json",
        "items_all": f"data/datasets/{DATASET_ID}/items.json",
        "n_documents": len(docs), "n_items": len(items),
        "n_dev": len(subsets["items_dev"]), "n_test": len(subsets["items_test"]),
        "split_policy": "Source URL separated: Apollo 8/9/10/17 only in test; seven other NASA/CDC pages only in dev. Test documents remain in retrieval corpus as required.",
        "annotator": "single author; no independent human review",
        "retrieved_date": DATE,
        "notes": "Frozen long-document retrieval slice. Four unanswerable and two benchmark-authored conflicting-document cases. No confirmatory or human-validated claims.",
    }
    path = Path(data_dir) / "manifests" / f"{DATASET_ID}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return str(directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data")
    print(write_dataset(parser.parse_args().output_dir))
