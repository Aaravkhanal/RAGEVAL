"""Licensed RAGeval benchmark v1: public-domain US government excerpts plus original CC-BY 4.0 text.

Rebuild JSON with: python -m rageval.dataset.benchmark_v1 --output-dir data
"""

from __future__ import annotations

import argparse
import json
import os
from typing import List, Tuple

from rageval.core.labels import VerificationLabel
from rageval.core.schemas import (
    BenchmarkItem,
    Document,
    GoldClaim,
    GoldEvidence,
    TestType,
)

DATASET_ID = "benchmark_v1"
DATASET_VERSION = "1.0.0"
RETRIEVED_DATE = "2026-10-28"
CC_BY = "CC-BY-4.0"
US_GOV_PD = "US-government-work-public-domain-17USC105"

# Typography in NASA HTML used curly quotes; stored text is ASCII-normalized.
NASA_OBJECTIVE = (
    "The primary objective of Apollo 11 was to complete a national goal set by President "
    "John F. Kennedy on May 25, 1961: perform a crewed lunar landing and return to Earth. "
    "Apollo 11 launched from Cape Kennedy on July 16, 1969, carrying Commander Neil Armstrong, "
    "Command Module Pilot Michael Collins and Lunar Module Pilot Edwin \"Buzz\" Aldrin into an "
    "initial Earth-orbit of 114 by 116 miles. An estimated 650 million people watched Armstrong's "
    "televised image and heard his voice describe the event as he took \"one small step for a man, "
    "one giant leap for mankind\" on July 20, 1969."
)

NASA_LANDING = (
    "Partially piloted manually by Armstrong, the Eagle landed in the Sea of Tranquility in Site 2 "
    "at 0 degrees, 41 minutes, 15 seconds north latitude and 23 degrees, 26 minutes east longitude. "
    "This was about four miles downrange from the predicted touchdown point and occurred almost "
    "one-and-a-half minutes earlier than scheduled. It included a powered descent that ran a mere "
    "nominal 40 seconds longer than preflight planning due to translation maneuvers to avoid a crater "
    "during the final phase of landing."
)

CDC_TYPES = (
    "There are four types of influenza viruses: A, B, C, and D. Influenza A and B viruses cause "
    "seasonal epidemics of disease in people (known as flu season) almost every winter in the "
    "United States. Influenza A viruses are the only influenza viruses known to cause flu pandemics "
    "(i.e., global epidemics of flu disease). Influenza C virus infections generally cause mild illness "
    "and are not thought to cause human epidemics. Influenza D viruses primarily affect cattle with "
    "spillover to other animals but are not known to cause illness in people."
)

CDC_SUBTYPES = (
    "Influenza A viruses are divided into subtypes based on two proteins on the surface of the virus: "
    "hemagglutinin (H) and neuraminidase (N). There are 18 hemagglutinin subtypes and 11 neuraminidase "
    "subtypes (H1 through H18 and N1 through N11, respectively). Current subtypes of influenza A viruses "
    "that routinely circulate in people include A(H1N1) and A(H3N2). Currently circulating influenza "
    "A(H1N1) viruses are descendants of the 2009 H1N1 pandemic virus that emerged in the spring of 2009 "
    "and caused a flu pandemic. B/Yamagata viruses have not been detected after March 2020."
)

NPS_ECOSYSTEM = (
    "Yellowstone National Park is as wondrous as it is complex. Established primarily to protect "
    "hydrothermal areas that contain about half the world's active geysers, the park also forms the "
    "core of the Greater Yellowstone Ecosystem. At 28,000 square miles, it is one of the largest, "
    "nearly intact temperate-zone ecosystems on Earth. It preserves a great variety of terrestrial, "
    "aquatic, and microbial life."
)

NPS_WILDLIFE = (
    "Learn about the park's abundant and diverse species—67 mammals, 285 birds, 16 fish, 5 amphibians, "
    "and 6 reptiles. Hydrothermal features are habitats for microscopic organisms called thermophiles: "
    '"thermo" for heat, "phile" for lover. Fire is a natural process and shapes the ecosystem.'
)

HARBORNET_Q2 = (
    "HarborNet reported subscription revenue of $412 million for the second quarter of 2025, a 9% "
    "increase from $378 million in Q2 2024. Average revenue per user was $54.10. Monthly churn was "
    "1.8%. Capital expenditure was $67 million, primarily for metro fiber laterals in Portland and Boise."
)

HARBORNET_BALANCE = (
    "As of June 30, 2025, HarborNet held cash and cash equivalents of $290 million and issued "
    "$640 million of senior notes due March 2031 at a 5.25% coupon. In May 2025 the board authorized "
    "an $80 million repurchase of Class B shares, of which $22 million was executed."
)

HARBORNET_GUIDANCE = (
    "For Q3 2025 HarborNet expects subscription revenue of $420 million to $428 million and monthly "
    "churn at or below 1.9%. Management capped fiber capital expenditure at $70 million for the quarter."
)

LUMENGRID_LATENCY = (
    "LumenGrid is a geo-sharded object store. Under a 90% read workload across four availability zones, "
    "median GET latency was 2.1 ms and p99 GET latency was 9.6 ms. Writes use a two-phase commit with "
    "a median PUT latency of 41 ms."
)

LUMENGRID_RECOVERY = (
    "LumenGrid crash recovery on a 200 GB shard completed in 6.4 seconds on NVMe. Failure detection "
    "uses a 300 ms heartbeat timeout and elects a new coordinator in 510 ms on average."
)

NEREXIN_TRIAL = (
    "In the Phase 3 SHORELINE trial (n=510), Nerexin plus pembrolizumab produced median progression-free "
    "survival of 11.2 months versus 6.4 months with pembrolizumab alone (hazard ratio 0.72; 95% CI "
    "0.58-0.89). Confirmed objective response rate was 44.0% versus 27.5%. Grade 3 or higher "
    "treatment-related adverse events occurred in 22.1% of the combination arm."
)

NEREXIN_PK = (
    "Nerexin is a humanized IgG4 antibody against OX40. The recommended dose is 6 mg/kg every four "
    "weeks. Terminal elimination half-life was 12.1 days. No dose-limiting toxicities were observed "
    "up to 12 mg/kg."
)

CEDARRAIL_PR = (
    "CedarRail opened unsupervised light-rail service in Tacoma in March 2025 with 40 driverless cars "
    "running 20 hours per day and zero passenger injuries in the first 60 days."
)

CEDARRAIL_AUDIT = (
    "The Pierce County transit audit found 12 of the advertised 40 CedarRail cars in revenue service "
    "as of June 2025 and required a licensed operator in every cab after three platform overruns in "
    "April 2025. Unsupervised service was suspended."
)

MILLFORD_LIBRARY = (
    "The Millford Public Library on Cedar Street is open Tuesday through Saturday from 10:00 a.m. to "
    "6:00 p.m. The local history room holds 14,000 cataloged photographs. Fines are $0.25 per day."
)


def _pd(
    doc_id: str,
    title: str,
    domain: str,
    text: str,
    source_url: str,
    provenance: str,
) -> Document:
    return Document(
        id=doc_id,
        title=title,
        domain=domain,
        text=text,
        license=US_GOV_PD,
        source_url=source_url,
        provenance=provenance,
        retrieved_date=RETRIEVED_DATE,
        metadata={"text_normalization": "ascii-quotes", "kind": "us_gov_excerpt"},
    )


def _orig(doc_id: str, title: str, domain: str, text: str) -> Document:
    return Document(
        id=doc_id,
        title=title,
        domain=domain,
        text=text,
        license=CC_BY,
        source_url=None,
        provenance="Original fiction written for RAGeval; entities are not real organizations.",
        retrieved_date=RETRIEVED_DATE,
        metadata={"kind": "original_synthetic", "license_note": "CC-BY-4.0"},
    )


def build_corpus() -> List[Document]:
    return [
        _pd(
            "doc_nasa_apollo11_objective",
            "Apollo 11 mission objective, launch, and crew",
            "space",
            NASA_OBJECTIVE,
            "https://www.nasa.gov/missions/apollo/apollo-11/apollo-11-mission-overview/",
            "Excerpt from NASA Apollo 11 Mission Overview (Sarah A. Loff, 2015-04-17). U.S. government work.",
        ),
        _pd(
            "doc_nasa_apollo11_landing",
            "Apollo 11 lunar landing site",
            "space",
            NASA_LANDING,
            "https://www.nasa.gov/missions/apollo/apollo-11/apollo-11-mission-overview/",
            "Excerpt from NASA Apollo 11 Mission Overview landing paragraph. U.S. government work.",
        ),
        _pd(
            "doc_cdc_flu_types",
            "Types of influenza viruses",
            "public_health",
            CDC_TYPES,
            "https://www.cdc.gov/flu/about/viruses-types.html",
            "Excerpt from CDC Types of Influenza Viruses (page date 2025-09-26). U.S. government work.",
        ),
        _pd(
            "doc_cdc_flu_subtypes",
            "Influenza A subtypes and B/Yamagata",
            "public_health",
            CDC_SUBTYPES,
            "https://www.cdc.gov/flu/about/viruses-types.html",
            "Excerpt from CDC Types of Influenza Viruses subtype section. U.S. government work.",
        ),
        _pd(
            "doc_nps_yellowstone_ecosystem",
            "Yellowstone hydrothermal areas and Greater Yellowstone Ecosystem",
            "parks",
            NPS_ECOSYSTEM,
            "https://www.nps.gov/yell/learn/nature/index.htm",
            "Excerpt from NPS Yellowstone Nature page (last updated 2025-04-18). U.S. government work.",
        ),
        _pd(
            "doc_nps_yellowstone_wildlife",
            "Yellowstone wildlife counts and thermophiles",
            "parks",
            NPS_WILDLIFE,
            "https://www.nps.gov/yell/learn/nature/index.htm",
            "Counts taken from the NPS Yellowstone Nature wildlife blurb on the same page. U.S. government work.",
        ),
        _orig("doc_harbornet_q2", "HarborNet Q2 2025 subscription results", "finance", HARBORNET_Q2),
        _orig("doc_harbornet_balance", "HarborNet cash, notes, and repurchase", "finance", HARBORNET_BALANCE),
        _orig("doc_harbornet_guidance", "HarborNet Q3 2025 guidance", "finance", HARBORNET_GUIDANCE),
        _orig("doc_lumengrid_latency", "LumenGrid GET/PUT latency", "systems", LUMENGRID_LATENCY),
        _orig("doc_lumengrid_recovery", "LumenGrid crash recovery", "systems", LUMENGRID_RECOVERY),
        _orig("doc_nerexin_trial", "Nerexin SHORELINE Phase 3 results", "biomedical", NEREXIN_TRIAL),
        _orig("doc_nerexin_pk", "Nerexin dose and pharmacokinetics", "biomedical", NEREXIN_PK),
        _orig("doc_cedarrail_pr", "CedarRail unsupervised service press note", "transit", CEDARRAIL_PR),
        _orig("doc_cedarrail_audit", "Pierce County CedarRail audit", "transit", CEDARRAIL_AUDIT),
        _orig("doc_millford_library", "Millford Public Library hours", "municipal", MILLFORD_LIBRARY),
    ]


def _ev(doc_id: str, span: str) -> GoldEvidence:
    return GoldEvidence(doc_id=doc_id, span=span)


def _claim(text: str, status: VerificationLabel, doc_ids: List[str]) -> GoldClaim:
    return GoldClaim(claim=text, status=status, gold_doc_ids=doc_ids)


def _item(
    item_id: str,
    domain: str,
    question: str,
    gold_answer: str | None,
    spans: List[GoldEvidence],
    claims: List[GoldClaim],
    *,
    test_type: TestType = TestType.STANDARD,
    expected_abstention: bool = False,
    answerability: str = "answerable",
    scenario_type: str = "standard",
    split: str = "dev",
    metadata: dict | None = None,
) -> BenchmarkItem:
    return BenchmarkItem(
        id=item_id,
        domain=domain,
        question=question,
        gold_answer=gold_answer,
        gold_evidence_spans=spans,
        gold_atomic_claims=claims,
        test_type=test_type,
        expected_abstention=expected_abstention,
        answerability=answerability,
        scenario_type=scenario_type,
        split=split,
        metadata=metadata or {},
    )


def build_items() -> List[BenchmarkItem]:
    test = "test"
    dev = "dev"
    return [
        _item(
            "v1_001",
            "space",
            "When did Apollo 11 launch, and who were the three crew members?",
            "Apollo 11 launched from Cape Kennedy on July 16, 1969, carrying Neil Armstrong, Michael Collins, and Edwin \"Buzz\" Aldrin.",
            [
                _ev(
                    "doc_nasa_apollo11_objective",
                    "Apollo 11 launched from Cape Kennedy on July 16, 1969, carrying Commander Neil Armstrong, Command Module Pilot Michael Collins and Lunar Module Pilot Edwin \"Buzz\" Aldrin",
                )
            ],
            [
                _claim("Apollo 11 launched on July 16, 1969", VerificationLabel.SUPPORTED, ["doc_nasa_apollo11_objective"]),
                _claim("The crew included Neil Armstrong, Michael Collins, and Edwin Buzz Aldrin", VerificationLabel.SUPPORTED, ["doc_nasa_apollo11_objective"]),
            ],
            split=dev,
        ),
        _item(
            "v1_002",
            "space",
            "Where did the Eagle land on the Moon?",
            "The Eagle landed in the Sea of Tranquility in Site 2 at 0 degrees, 41 minutes, 15 seconds north latitude and 23 degrees, 26 minutes east longitude.",
            [
                _ev(
                    "doc_nasa_apollo11_landing",
                    "the Eagle landed in the Sea of Tranquility in Site 2 at 0 degrees, 41 minutes, 15 seconds north latitude and 23 degrees, 26 minutes east longitude.",
                )
            ],
            [
                _claim("The Eagle landed in the Sea of Tranquility", VerificationLabel.SUPPORTED, ["doc_nasa_apollo11_landing"]),
                _claim("The landing site was Site 2", VerificationLabel.SUPPORTED, ["doc_nasa_apollo11_landing"]),
            ],
            split=test,
        ),
        _item(
            "v1_003",
            "public_health",
            "Which influenza virus types cause seasonal epidemics in people in the United States?",
            "Influenza A and B viruses cause seasonal epidemics of disease in people almost every winter in the United States.",
            [
                _ev(
                    "doc_cdc_flu_types",
                    "Influenza A and B viruses cause seasonal epidemics of disease in people (known as flu season) almost every winter in the United States.",
                )
            ],
            [
                _claim("Influenza A viruses cause seasonal epidemics in people", VerificationLabel.SUPPORTED, ["doc_cdc_flu_types"]),
                _claim("Influenza B viruses cause seasonal epidemics in people", VerificationLabel.SUPPORTED, ["doc_cdc_flu_types"]),
            ],
            split=dev,
        ),
        _item(
            "v1_004",
            "public_health",
            "Which influenza A subtypes routinely circulate in people, and do influenza D viruses cause illness in people?",
            "Current subtypes that routinely circulate in people include A(H1N1) and A(H3N2). Influenza D viruses are not known to cause illness in people.",
            [
                _ev(
                    "doc_cdc_flu_subtypes",
                    "Current subtypes of influenza A viruses that routinely circulate in people include A(H1N1) and A(H3N2).",
                ),
                _ev(
                    "doc_cdc_flu_types",
                    "Influenza D viruses primarily affect cattle with spillover to other animals but are not known to cause illness in people.",
                ),
            ],
            [
                _claim("A(H1N1) and A(H3N2) routinely circulate in people", VerificationLabel.SUPPORTED, ["doc_cdc_flu_subtypes"]),
                _claim("Influenza D viruses are not known to cause illness in people", VerificationLabel.SUPPORTED, ["doc_cdc_flu_types"]),
            ],
            split=dev,
        ),
        _item(
            "v1_005",
            "parks",
            "Why was Yellowstone National Park established, and how large is the Greater Yellowstone Ecosystem?",
            "Yellowstone was established primarily to protect hydrothermal areas that contain about half the world's active geysers. The Greater Yellowstone Ecosystem is 28,000 square miles.",
            [
                _ev(
                    "doc_nps_yellowstone_ecosystem",
                    "Established primarily to protect hydrothermal areas that contain about half the world's active geysers, the park also forms the core of the Greater Yellowstone Ecosystem. At 28,000 square miles, it is one of the largest, nearly intact temperate-zone ecosystems on Earth.",
                )
            ],
            [
                _claim("Yellowstone was established primarily to protect hydrothermal areas", VerificationLabel.SUPPORTED, ["doc_nps_yellowstone_ecosystem"]),
                _claim("Those areas contain about half the world's active geysers", VerificationLabel.SUPPORTED, ["doc_nps_yellowstone_ecosystem"]),
                _claim("The Greater Yellowstone Ecosystem is 28,000 square miles", VerificationLabel.SUPPORTED, ["doc_nps_yellowstone_ecosystem"]),
            ],
            split=dev,
        ),
        _item(
            "v1_006",
            "parks",
            "How many mammal and bird species does Yellowstone preserve according to the Nature page?",
            "The Nature page lists 67 mammals and 285 birds.",
            [
                _ev(
                    "doc_nps_yellowstone_wildlife",
                    "Learn about the park's abundant and diverse species—67 mammals, 285 birds, 16 fish, 5 amphibians, and 6 reptiles.",
                )
            ],
            [
                _claim("The park has 67 mammal species", VerificationLabel.SUPPORTED, ["doc_nps_yellowstone_wildlife"]),
                _claim("The park has 285 bird species", VerificationLabel.SUPPORTED, ["doc_nps_yellowstone_wildlife"]),
            ],
            split=test,
        ),
        _item(
            "v1_007",
            "finance",
            "What was HarborNet's Q2 2025 subscription revenue and monthly churn?",
            "HarborNet reported subscription revenue of $412 million for Q2 2025 and monthly churn of 1.8%.",
            [
                _ev(
                    "doc_harbornet_q2",
                    "HarborNet reported subscription revenue of $412 million for the second quarter of 2025, a 9% increase from $378 million in Q2 2024. Average revenue per user was $54.10. Monthly churn was 1.8%.",
                )
            ],
            [
                _claim("HarborNet Q2 2025 subscription revenue was $412 million", VerificationLabel.SUPPORTED, ["doc_harbornet_q2"]),
                _claim("Monthly churn was 1.8%", VerificationLabel.SUPPORTED, ["doc_harbornet_q2"]),
            ],
            split=dev,
        ),
        _item(
            "v1_008",
            "finance",
            "How much senior notes does HarborNet have, when do they mature, and how much of the May 2025 repurchase was executed?",
            "HarborNet issued $640 million of senior notes due March 2031. Of an $80 million Class B repurchase authorization, $22 million was executed.",
            [
                _ev(
                    "doc_harbornet_balance",
                    "issued $640 million of senior notes due March 2031 at a 5.25% coupon. In May 2025 the board authorized an $80 million repurchase of Class B shares, of which $22 million was executed.",
                )
            ],
            [
                _claim("HarborNet issued $640 million of senior notes due March 2031", VerificationLabel.SUPPORTED, ["doc_harbornet_balance"]),
                _claim("$22 million of the Class B repurchase was executed", VerificationLabel.SUPPORTED, ["doc_harbornet_balance"]),
            ],
            split=test,
        ),
        _item(
            "v1_009",
            "systems",
            "What are LumenGrid's median and p99 GET latencies under the reported read-heavy workload?",
            "Median GET latency was 2.1 ms and p99 GET latency was 9.6 ms.",
            [
                _ev(
                    "doc_lumengrid_latency",
                    "median GET latency was 2.1 ms and p99 GET latency was 9.6 ms.",
                )
            ],
            [
                _claim("LumenGrid median GET latency was 2.1 ms", VerificationLabel.SUPPORTED, ["doc_lumengrid_latency"]),
                _claim("LumenGrid p99 GET latency was 9.6 ms", VerificationLabel.SUPPORTED, ["doc_lumengrid_latency"]),
            ],
            split=dev,
        ),
        _item(
            "v1_010",
            "systems",
            "How long did LumenGrid crash recovery take on a 200 GB shard, and what is the heartbeat timeout?",
            "Crash recovery on a 200 GB shard completed in 6.4 seconds. Failure detection uses a 300 ms heartbeat timeout.",
            [
                _ev(
                    "doc_lumengrid_recovery",
                    "LumenGrid crash recovery on a 200 GB shard completed in 6.4 seconds on NVMe. Failure detection uses a 300 ms heartbeat timeout",
                )
            ],
            [
                _claim("Recovery of a 200 GB shard completed in 6.4 seconds", VerificationLabel.SUPPORTED, ["doc_lumengrid_recovery"]),
                _claim("Heartbeat timeout is 300 ms", VerificationLabel.SUPPORTED, ["doc_lumengrid_recovery"]),
            ],
            split=dev,
        ),
        _item(
            "v1_011",
            "biomedical",
            "What was median PFS and confirmed ORR for Nerexin plus pembrolizumab in SHORELINE?",
            "Median progression-free survival was 11.2 months and confirmed objective response rate was 44.0% in the combination arm.",
            [
                _ev(
                    "doc_nerexin_trial",
                    "Nerexin plus pembrolizumab produced median progression-free survival of 11.2 months versus 6.4 months with pembrolizumab alone (hazard ratio 0.72; 95% CI 0.58-0.89). Confirmed objective response rate was 44.0% versus 27.5%.",
                )
            ],
            [
                _claim("Median PFS was 11.2 months for Nerexin plus pembrolizumab", VerificationLabel.SUPPORTED, ["doc_nerexin_trial"]),
                _claim("Confirmed ORR was 44.0% in the combination arm", VerificationLabel.SUPPORTED, ["doc_nerexin_trial"]),
            ],
            split=dev,
        ),
        _item(
            "v1_012",
            "finance",
            "What subscription revenue range did HarborNet guide for Q3 2025?",
            "HarborNet expects subscription revenue of $420 million to $428 million for Q3 2025.",
            [
                _ev(
                    "doc_harbornet_guidance",
                    "For Q3 2025 HarborNet expects subscription revenue of $420 million to $428 million",
                )
            ],
            [
                _claim("Q3 2025 subscription revenue guidance is $420 million to $428 million", VerificationLabel.SUPPORTED, ["doc_harbornet_guidance"]),
            ],
            split=test,
        ),
        _item(
            "v1_013",
            "space",
            "What meals did the Apollo 11 crew eat during translunar coast?",
            None,
            [],
            [],
            test_type=TestType.UNANSWERABLE,
            expected_abstention=True,
            answerability="unanswerable",
            scenario_type="unanswerable",
            split=dev,
            metadata={"adversarial_reason": "The excerpts describe launch, crew, and landing; they do not list meals."},
        ),
        _item(
            "v1_014",
            "finance",
            "What share of HarborNet Q2 2025 revenue came from Japanese enterprise customers?",
            None,
            [],
            [],
            test_type=TestType.UNANSWERABLE,
            expected_abstention=True,
            answerability="unanswerable",
            scenario_type="unanswerable",
            split=dev,
            metadata={"adversarial_reason": "HarborNet reports total subscription revenue, not a Japan split."},
        ),
        _item(
            "v1_015",
            "parks",
            "How many recreational visits did Yellowstone record in calendar year 2024?",
            None,
            [],
            [],
            test_type=TestType.UNANSWERABLE,
            expected_abstention=True,
            answerability="unanswerable",
            scenario_type="unanswerable",
            split=dev,
            metadata={"adversarial_reason": "The Nature page excerpts do not state 2024 visitation."},
        ),
        _item(
            "v1_016",
            "biomedical",
            "What was the 5-year overall survival for pediatric patients treated with Nerexin?",
            None,
            [],
            [],
            test_type=TestType.UNANSWERABLE,
            expected_abstention=True,
            answerability="unanswerable",
            scenario_type="unanswerable",
            split=test,
            metadata={"adversarial_reason": "SHORELINE reports adult PFS/ORR; pediatric 5-year OS is absent."},
        ),
        _item(
            "v1_017",
            "transit",
            "Did CedarRail operate unsupervised light-rail cars in Tacoma without licensed operators?",
            "Sources conflict. The press note says CedarRail opened unsupervised service with 40 driverless cars. The Pierce County audit required a licensed operator in every cab and suspended unsupervised service.",
            [
                _ev(
                    "doc_cedarrail_pr",
                    "CedarRail opened unsupervised light-rail service in Tacoma in March 2025 with 40 driverless cars",
                ),
                _ev(
                    "doc_cedarrail_audit",
                    "required a licensed operator in every cab after three platform overruns in April 2025. Unsupervised service was suspended.",
                ),
            ],
            [
                _claim("The press note claimed unsupervised driverless service", VerificationLabel.SUPPORTED, ["doc_cedarrail_pr"]),
                _claim("The audit required a licensed operator in every cab", VerificationLabel.SUPPORTED, ["doc_cedarrail_audit"]),
            ],
            test_type=TestType.CONFLICTING,
            scenario_type="conflicting",
            split=dev,
            metadata={"conflict_docs": ["doc_cedarrail_pr", "doc_cedarrail_audit"]},
        ),
        _item(
            "v1_018",
            "transit",
            "How many CedarRail cars were in revenue service?",
            "Sources conflict. The press note advertised 40 driverless cars; the audit found 12 of the advertised 40 cars in revenue service as of June 2025.",
            [
                _ev("doc_cedarrail_pr", "with 40 driverless cars running 20 hours per day"),
                _ev(
                    "doc_cedarrail_audit",
                    "The Pierce County transit audit found 12 of the advertised 40 CedarRail cars in revenue service as of June 2025",
                ),
            ],
            [
                _claim("The press note advertised 40 driverless cars", VerificationLabel.SUPPORTED, ["doc_cedarrail_pr"]),
                _claim("The audit found 12 cars in revenue service as of June 2025", VerificationLabel.SUPPORTED, ["doc_cedarrail_audit"]),
            ],
            test_type=TestType.CONFLICTING,
            scenario_type="conflicting",
            split=test,
            metadata={"conflict_docs": ["doc_cedarrail_pr", "doc_cedarrail_audit"]},
        ),
        _item(
            "v1_019",
            "public_health",
            "Which influenza virus types cause seasonal epidemics in people in the United States?",
            "Influenza A and B viruses cause seasonal epidemics of disease in people almost every winter in the United States.",
            [
                _ev(
                    "doc_cdc_flu_types",
                    "Influenza A and B viruses cause seasonal epidemics of disease in people (known as flu season) almost every winter in the United States.",
                )
            ],
            [
                _claim("Influenza A and B viruses cause seasonal epidemics in people", VerificationLabel.SUPPORTED, ["doc_cdc_flu_types"]),
                _claim("Influenza D viruses cause seasonal epidemics in people", VerificationLabel.CONTRADICTED, ["doc_cdc_flu_types"]),
            ],
            scenario_type="mixed_support",
            split=dev,
            metadata={
                "example_mixed_answer": (
                    "Influenza A and B viruses cause seasonal epidemics of disease in people almost every winter "
                    "in the United States. Influenza D viruses also cause seasonal epidemics in people."
                ),
                "rq3_note": "Token F1 vs gold stays high if the mixed sentence is appended; claim labels are mixed.",
            },
        ),
        _item(
            "v1_020",
            "space",
            "Where did the Eagle land on the Moon?",
            "The Eagle landed in the Sea of Tranquility in Site 2 at 0 degrees, 41 minutes, 15 seconds north latitude and 23 degrees, 26 minutes east longitude.",
            [
                _ev(
                    "doc_nasa_apollo11_landing",
                    "the Eagle landed in the Sea of Tranquility in Site 2 at 0 degrees, 41 minutes, 15 seconds north latitude and 23 degrees, 26 minutes east longitude.",
                )
            ],
            [
                _claim("The Eagle landed in the Sea of Tranquility", VerificationLabel.SUPPORTED, ["doc_nasa_apollo11_landing"]),
                _claim("Armstrong remained on the lunar surface for 14 days", VerificationLabel.UNSUPPORTED, []),
            ],
            scenario_type="mixed_support",
            split=test,
            metadata={
                "example_mixed_answer": (
                    "The Eagle landed in the Sea of Tranquility in Site 2 at 0 degrees, 41 minutes, 15 seconds "
                    "north latitude and 23 degrees, 26 minutes east longitude. Armstrong remained on the lunar surface for 14 days."
                ),
            },
        ),
        _item(
            "v1_021",
            "finance",
            "What was HarborNet's Q2 2025 subscription revenue?",
            "HarborNet reported subscription revenue of $412 million for the second quarter of 2025.",
            [
                _ev(
                    "doc_harbornet_q2",
                    "HarborNet reported subscription revenue of $412 million for the second quarter of 2025",
                )
            ],
            [
                _claim("HarborNet Q2 2025 subscription revenue was $412 million", VerificationLabel.SUPPORTED, ["doc_harbornet_q2"]),
                _claim("HarborNet employed 48,000 people in Osaka", VerificationLabel.UNSUPPORTED, []),
            ],
            scenario_type="mixed_support",
            split=dev,
            metadata={
                "example_mixed_answer": (
                    "HarborNet reported subscription revenue of $412 million for the second quarter of 2025 "
                    "and employed 48,000 people in Osaka."
                ),
            },
        ),
        _item(
            "v1_022",
            "parks",
            "Does Yellowstone contain hydrothermal features?",
            "Yellowstone was established primarily to protect hydrothermal areas that contain about half the world's active geysers.",
            [
                _ev(
                    "doc_nps_yellowstone_ecosystem",
                    "Established primarily to protect hydrothermal areas that contain about half the world's active geysers",
                )
            ],
            [
                _claim("Yellowstone contains hydrothermal areas with many active geysers", VerificationLabel.SUPPORTED, ["doc_nps_yellowstone_ecosystem"]),
                _claim("Yellowstone contains no hydrothermal features", VerificationLabel.CONTRADICTED, ["doc_nps_yellowstone_ecosystem"]),
            ],
            scenario_type="mixed_support",
            split=dev,
            metadata={
                "example_mixed_answer": (
                    "Yellowstone was established primarily to protect hydrothermal areas that contain about half "
                    "the world's active geysers. Yellowstone contains no hydrothermal features."
                ),
            },
        ),
        _item(
            "v1_023",
            "finance",
            "What was HarborNet monthly churn in Q2 2025?",
            "Monthly churn was 1.8%.",
            [
                _ev("doc_harbornet_q2", "Monthly churn was 1.8%."),
            ],
            [
                _claim("Monthly churn was 1.8%", VerificationLabel.SUPPORTED, ["doc_harbornet_q2"]),
            ],
            test_type=TestType.DISTRACTOR,
            scenario_type="distractor",
            split=dev,
            metadata={"distractor_docs": ["doc_millford_library", "doc_nerexin_trial"]},
        ),
        _item(
            "v1_024",
            "public_health",
            "Are influenza A viruses the only influenza viruses known to cause flu pandemics?",
            "Yes. Influenza A viruses are the only influenza viruses known to cause flu pandemics.",
            [
                _ev(
                    "doc_cdc_flu_types",
                    "Influenza A viruses are the only influenza viruses known to cause flu pandemics",
                )
            ],
            [
                _claim("Influenza A viruses are the only influenza viruses known to cause flu pandemics", VerificationLabel.SUPPORTED, ["doc_cdc_flu_types"]),
            ],
            test_type=TestType.DISTRACTOR,
            scenario_type="distractor",
            split=test,
            metadata={"distractor_docs": ["doc_millford_library", "doc_harbornet_q2"]},
        ),
    ]


def build_benchmark() -> Tuple[List[Document], List[BenchmarkItem]]:
    return build_corpus(), build_items()


def _dump(path: str, payload) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


def write_dataset(data_dir: str = "data") -> str:
    documents, items = build_benchmark()
    out_dir = os.path.join(data_dir, "datasets", DATASET_ID)
    os.makedirs(out_dir, exist_ok=True)

    def dump_docs():
        return [d.model_dump() for d in documents]

    def dump_items(subset: List[BenchmarkItem]):
        return [i.model_dump(mode="json") for i in subset]

    _dump(os.path.join(out_dir, "corpus.json"), dump_docs())
    _dump(os.path.join(out_dir, "items.json"), dump_items(items))
    _dump(
        os.path.join(out_dir, "items_dev.json"),
        dump_items([i for i in items if i.split == "dev"]),
    )
    _dump(
        os.path.join(out_dir, "items_test.json"),
        dump_items([i for i in items if i.split == "test"]),
    )
    _dump(
        os.path.join(out_dir, "items_standard.json"),
        dump_items([i for i in items if i.test_type == TestType.STANDARD]),
    )
    _dump(
        os.path.join(out_dir, "items_adversarial.json"),
        dump_items(
            [
                i
                for i in items
                if i.test_type in {TestType.UNANSWERABLE, TestType.CONFLICTING, TestType.DISTRACTOR}
            ]
        ),
    )

    n_dev = sum(1 for i in items if i.split == "dev")
    n_test = sum(1 for i in items if i.split == "test")
    manifest = {
        "dataset_id": DATASET_ID,
        "version": DATASET_VERSION,
        "synthetic": False,
        "license": "mixed: US-government-work-public-domain-17USC105 and CC-BY-4.0 original fiction",
        "documents": f"data/datasets/{DATASET_ID}/corpus.json",
        "items_all": f"data/datasets/{DATASET_ID}/items.json",
        "items_dev": f"data/datasets/{DATASET_ID}/items_dev.json",
        "items_test": f"data/datasets/{DATASET_ID}/items_test.json",
        "n_documents": len(documents),
        "n_items": len(items),
        "n_dev": n_dev,
        "n_test": n_test,
        "split_policy": (
            "Documented 16/8 dev/test split. The first ablation reports the full 24-item set because "
            "n_test=8 is underpowered. Test items were not used to choose metrics or NLI thresholds."
        ),
        "annotator": "single-author, disclosed",
        "retrieved_date": RETRIEVED_DATE,
        "notes": (
            "Public-domain excerpts are short US government passages with URL provenance. "
            "HarborNet, LumenGrid, Nerexin, CedarRail, and Millford are original fiction (CC-BY-4.0). "
            "NASA quotes were ASCII-normalized. This is not the Niu et al. 2024 RAGTruth corpus."
        ),
    }
    _dump(os.path.join(data_dir, "manifests", f"{DATASET_ID}.json"), manifest)
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Write licensed benchmark_v1 JSON")
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()
    path = write_dataset(args.output_dir)
    print(f"Wrote {DATASET_ID} under {path}")


if __name__ == "__main__":
    main()
