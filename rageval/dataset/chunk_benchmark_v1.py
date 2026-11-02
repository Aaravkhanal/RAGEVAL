"""Pinned public-document slice for testing fixed-size chunk retrieval.

Rebuild with ``python -m rageval.dataset.chunk_benchmark_v1 --output-dir data``.
The source snapshots are checked in; rebuilding does not fetch changing web pages.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from rageval.core.assets import resolve_asset
from rageval.core.labels import VerificationLabel
from rageval.core.schemas import BenchmarkItem, Document, GoldClaim, GoldEvidence

DATASET_ID = "chunk_benchmark_v1"
DATASET_VERSION = "1.0.0"
RETRIEVED_DATE = "2026-11-02"
LICENSE = "US-government-work-public-domain-17USC105"

SOURCES = (
    ("apollo11", "Apollo 11 Mission Overview", "space", "https://www.nasa.gov/missions/apollo/apollo-11-mission-overview/"),
    ("influenza", "Types of Influenza Viruses", "public_health", "https://www.cdc.gov/flu/about/viruses-types.html"),
    ("apollo13", "Apollo 13 Mission Details", "space", "https://www.nasa.gov/missions/apollo/apollo-13-mission-details/"),
    ("apollo14", "Apollo 14 Mission Details", "space", "https://www.nasa.gov/missions/apollo/apollo-14-mission-details/"),
    ("apollo15", "Apollo 15 Mission Details", "space", "https://www.nasa.gov/missions/apollo/apollo-15-mission-details/"),
    ("apollo16", "Apollo 16 Mission Details", "space", "https://www.nasa.gov/missions/apollo/apollo-16-mission-details/"),
    ("flu_change", "How Flu Viruses Can Change", "public_health", "https://www.cdc.gov/flu/php/viruses/change.html"),
)

# (source, question, answer, verbatim evidence). Questions were authored for this
# diagnostic slice and have not received independent human annotation.
QUESTIONS = (
    ("apollo11", "What national goal was Apollo 11's primary objective?", "A crewed lunar landing and return to Earth.", "perform a crewed lunar landing and return to Earth"),
    ("apollo11", "When and from where did Apollo 11 launch?", "July 16, 1969, from Cape Kennedy.", "Apollo 11 launched from Cape Kennedy on July 16, 1969"),
    ("apollo11", "When did Apollo 11 first transmit color TV to Earth?", "During the translunar coast.", "The first color TV transmission to Earth from Apollo 11 occurred during the translunar coast"),
    ("apollo11", "What was Apollo 11's initial elliptical lunar orbit?", "69 by 190 miles.", "an initial, elliptical-lunar orbit of 69 by 190 miles"),
    ("apollo11", "How far downrange from the predicted point did Eagle land?", "About four miles.", "about four miles downrange from the predicted touchdown point"),
    ("apollo11", "How long did Armstrong and Aldrin spend on the moon's surface?", "21 hours, 36 minutes.", "Armstrong and Aldrin spent 21 hours, 36 minutes on the moon’s surface"),
    ("apollo11", "How far from the recovery ship did Apollo 11 splash down?", "13 miles from USS Hornet.", "Apollo 11 splashed down in the Pacific Ocean, 13 miles from the recovery ship USS Hornet"),
    ("influenza", "What are the four types of influenza viruses?", "A, B, C, and D.", "There are four types of influenza viruses: A, B, C, and D"),
    ("influenza", "Which influenza virus type is known to cause flu pandemics?", "Influenza A.", "Influenza A viruses are the only influenza viruses known to cause flu pandemics"),
    ("influenza", "Are influenza D viruses known to cause illness in people?", "No; they primarily affect cattle and are not known to cause illness in people.", "Influenza D viruses primarily affect cattle with spillover to other animals but are not known to cause illness in people"),
    ("influenza", "How many hemagglutinin and neuraminidase subtypes are there?", "18 hemagglutinin and 11 neuraminidase subtypes.", "There are 18 hemagglutinin subtypes and 11 neuraminidase subtypes"),
    ("influenza", "Which influenza A subtypes routinely circulate in people?", "A(H1N1) and A(H3N2).", "Current subtypes of influenza A viruses that routinely circulate in people include A(H1N1) and A(H3N2)"),
    ("influenza", "When were B/Yamagata viruses last detected?", "They have not been detected after March 2020.", "B/Yamagata viruses have not been detected after March 2020"),
    ("influenza", "Which three viruses do US seasonal flu vaccines target?", "One A(H1N1), one A(H3N2), and one B/Victoria lineage virus.", "one influenza A(H1N1) virus, one influenza A(H3N2) virus, and one influenza B/Victoria lineage virus"),
    ("apollo13", "Which lunar region was Apollo 13 supposed to visit?", "Fra Mauro.", "Apollo 13 was supposed to land in the Fra Mauro area"),
    ("apollo13", "Who replaced Ken Mattingly as Apollo 13 command module pilot?", "John Jack Swigert.", "was replaced by backup command module pilot, John “Jack” Swigert"),
    ("apollo13", "What happened to Apollo 13 oxygen tank No. 2?", "It blew up, causing tank No. 1 to fail too.", "oxygen tank No. 2 blew up, causing the No. 1 tank to also fail"),
    ("apollo13", "How did mission control adapt carbon dioxide canisters for Apollo 13?", "It attached command module canisters to the lunar module system with plastic bags, cardboard, and tape.", "Mission control devised a way to attach the CM canisters to the LM system by using plastic bags, cardboard and to tape"),
    ("apollo14", "Which region was Apollo 14 sent to explore?", "The Fra Mauro region.", "explore the Fra Mauro region"),
    ("apollo14", "How close did Apollo 14's Antares land to its target?", "Approximately 87 feet.", "Antares made the most precise landing to date, approximately 87 feet from the targeted landing point"),
    ("apollo14", "How much rock and soil did Apollo 14 astronauts collect?", "94 pounds.", "the astronauts collected 94 pounds of rocks and soil for return to Earth"),
    ("apollo15", "Which vehicle enhanced Apollo 15 surface investigations?", "The Lunar Roving Vehicle.", "enhanced by the addition of the Lunar Roving Vehicle"),
    ("apollo15", "Where did Apollo 15 land?", "At Hadley Rille.", "landing at 6:16 p.m. EDT July 30, at Hadley Rille"),
    ("apollo15", "How far did Apollo 15 astronauts travel in the lunar rover?", "17.5 miles.", "traveled 17.5 miles in the first car that humans have ever driven on the moon"),
    ("apollo16", "Which highlands formations was the Apollo 16 landing site chosen to sample?", "The Cayley formation and Kant Plateau.", "the Cayley formation and the Kant Plateau"),
    ("apollo16", "Who landed Apollo 16's lunar module at Descartes?", "John Young and Charles Duke.", "carrying John Young and Charles Duke touched down at Descartes"),
    ("apollo16", "What shortened the Apollo 16 subsatellite's expected life?", "Deletion of the orbital shaping maneuver left it in a highly elliptical orbit.", "it was ejected into a highly elliptical orbit, cutting its lifetime from one year to about one month"),
    ("flu_change", "What changes cause antigenic drift?", "Small mutations in influenza-virus genes that can change HA and NA proteins.", "Drift consists of small changes (or mutations) in the genes of influenza viruses"),
    ("flu_change", "Why are flu-vaccine compositions reviewed annually?", "To keep up with evolving viruses changed by antigenic drift.", "the composition of flu vaccines for use in the Northern and Southern Hemispheres is reviewed annually and updated as needed"),
    ("flu_change", "What is antigenic shift?", "An abrupt major change in an influenza A virus that creates new HA or HA and NA proteins.", "Shift is an abrupt, major change in a flu A virus, resulting in new HA and/or new HA and NA proteins"),
)


def _source_path(source: str) -> Path:
    return Path(resolve_asset(f"data/datasets/{DATASET_ID}/sources/{source}.txt"))


def build_benchmark() -> tuple[list[Document], list[BenchmarkItem]]:
    documents: list[Document] = []
    for source, title, domain, url in SOURCES:
        path = _source_path(source)
        text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8")).strip()
        documents.append(
            Document(
                id=f"doc_{source}",
                title=title,
                domain=domain,
                text=text,
                license=LICENSE,
                source_url=url,
                provenance=f"Pinned main-content paragraph snapshot from {url} on {RETRIEVED_DATE}.",
                retrieved_date=RETRIEVED_DATE,
                metadata={"source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "kind": "us_gov_snapshot"},
            )
        )
    by_source = {doc.id.removeprefix("doc_"): doc for doc in documents}
    items: list[BenchmarkItem] = []
    for index, (source, question, answer, evidence) in enumerate(QUESTIONS, start=1):
        document = by_source[source]
        if evidence not in document.text:
            raise ValueError(f"Evidence for chunk item {index} is absent from {document.id}")
        items.append(
            BenchmarkItem(
                id=f"chunk_{index:03d}",
                domain=document.domain or "general",
                question=question,
                gold_answer=answer,
                gold_evidence_spans=[GoldEvidence(doc_id=document.id, span=evidence)],
                gold_atomic_claims=[GoldClaim(claim=answer, status=VerificationLabel.SUPPORTED, gold_doc_ids=[document.id])],
                split="dev",
                metadata={"annotation_status": "single_author_diagnostic"},
            )
        )
    return documents, items


def write_dataset(data_dir: str = "data") -> str:
    documents, items = build_benchmark()
    directory = Path(data_dir) / "datasets" / DATASET_ID
    directory.mkdir(parents=True, exist_ok=True)

    def dump(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    dump(directory / "corpus.json", [doc.model_dump() for doc in documents])
    for name, subset in (
        ("items.json", items),
        ("items_dev.json", items),
        ("items_test.json", []),
        ("items_standard.json", items),
        ("items_adversarial.json", []),
        ("items_independent.json", []),
    ):
        dump(directory / name, [item.model_dump(mode="json") for item in subset])
    dump(Path(data_dir) / "manifests" / f"{DATASET_ID}.json", {
        "dataset_id": DATASET_ID,
        "version": DATASET_VERSION,
        "synthetic": False,
        "license": LICENSE,
        "documents": f"data/datasets/{DATASET_ID}/corpus.json",
        "items_all": f"data/datasets/{DATASET_ID}/items.json",
        "n_documents": len(documents),
        "n_items": len(items),
        "n_dev": len(items),
        "n_test": 0,
        "split_policy": "Diagnostic chunk-size slice: all items are dev; no held-out or independent test set.",
        "annotator": "single-author, diagnostic",
        "retrieved_date": RETRIEVED_DATE,
        "notes": "Long public NASA and CDC main-content snapshots. Evaluate evidence-span recall, not only document recall. No confirmatory claims.",
    })
    return str(directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rebuild pinned chunk benchmark JSON")
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()
    print(write_dataset(args.output_dir))
