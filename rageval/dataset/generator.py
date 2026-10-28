"""Corpus and benchmark dataset generator with multi-domain data and adversarial edge cases."""

from __future__ import annotations
import json
import os
from typing import List, Dict, Tuple
from rageval.core.schemas import (
    Document,
    BenchmarkItem,
    GoldEvidence,
    GoldClaim,
    TestType,
    VerificationLabel,
)


def create_synthetic_benchmark() -> Tuple[List[Document], List[BenchmarkItem]]:
    """Creates a curated research benchmark with gold documents, Q&A pairs,

    gold atomic claims, and adversarial edge cases (unanswerables & conflicting documents).
    """

    # 1. Corpus Documents
    documents = [
        # Domain: Finance / Enterprise Tech
        Document(
            id="doc_fin_01",
            title="ApexCloud Q3 2024 Financial Performance & Guidance",
            domain="finance",
            text=(
                "ApexCloud reported total revenue of $842 million for the third quarter of 2024, "
                "representing a 24% year-over-year growth. Non-GAAP gross margin expanded by 180 basis points "
                "to 78.2%, driven by custom ASIC silicon deployment across edge datacenters. Operating cash flow "
                "reached $215 million, compared to $145 million in Q3 2023. Net retention rate stood at 119%, "
                "moderating slightly from 122% in the prior quarter due to enterprise budget scrutiny in EMEA. "
                "For Q4 2024, management expects revenue between $880 million and $890 million with capital "
                "expenditures capped at $95 million."
            ),
            metadata={"quarter": "Q3 2024", "ticker": "APEX", "source": "10-Q filing"},
        ),
        Document(
            id="doc_fin_02",
            title="ApexCloud Long-Term Debt and Capital Structure",
            domain="finance",
            text=(
                "As of September 30, 2024, ApexCloud held total cash, cash equivalents, and marketable securities "
                "of $1.85 billion against total senior unsecured notes of $1.20 billion maturing in October 2029. "
                "The notes carry a fixed coupon rate of 3.875% payable semi-annually. In August 2024, the company "
                "repurchased $150 million in Class A common stock under its existing $500 million share repurchase authorization."
            ),
            metadata={"filing": "Debt Note 7", "source": "SEC Edgar"},
        ),
        
        # Domain: Biomedical / Pharmacology
        Document(
            id="doc_bio_01",
            title="Phase 3 Clinical Evaluation of Veloceptin in Metastatic Melanoma",
            domain="biomedical",
            text=(
                "In the randomized double-blind Phase 3 RADIANT-4 trial (n=742), Veloceptin combined with nivolumab "
                "demonstrated a median progression-free survival (PFS) of 14.8 months versus 8.2 months with nivolumab "
                "monotherapy (hazard ratio 0.61; 95% CI 0.49-0.75; p < 0.001). The confirmed objective response rate (ORR) "
                "was 58.4% in the combination cohort compared to 36.1% in the control arm. Grade 3 or higher treatment-related "
                "adverse events occurred in 31.2% of patients receiving combination therapy, predominantly manifested as elevated "
                "alanine aminotransferase (ALT) and immune-mediated colitis. Discontinuation due to adverse events was 9.4%."
            ),
            metadata={"trial_id": "NCT04892110", "phase": "Phase 3", "journal": "NEJM Oncology"},
        ),
        Document(
            id="doc_bio_02",
            title="Pharmacokinetics and Dosing Tolerability of Veloceptin",
            domain="biomedical",
            text=(
                "Veloceptin is a humanized monoclonal IgG1-kappa antibody targeting immunosuppressive receptor Siglec-15. "
                "Following intravenous infusion at the recommended phase 2/3 dose of 10 mg/kg every three weeks, terminal "
                "elimination half-life was 18.4 days with steady-state concentration achieved by cycle 4. No dose-limiting "
                "toxicities were observed up to 20 mg/kg."
            ),
            metadata={"molecule": "Veloceptin", "target": "Siglec-15"},
        ),

        # Domain: Distributed Systems / Computer Science
        Document(
            id="doc_cs_01",
            title="HydraKV: Consensus Protocol and Latency Benchmarks",
            domain="systems",
            text=(
                "HydraKV is a geo-replicated distributed key-value store utilizing a quorum-lease consensus protocol "
                "optimized for read-heavy workloads. Under uniform 95% read traffic across 5 planetary regions, HydraKV "
                "achieved a median read latency of 1.4 ms and a 99th percentile (p99) read latency of 4.8 ms by servicing reads "
                "locally via monotonic read lease grants. Write operations require strict majority quorum consensus with Raft, "
                "yielding a median write latency of 74.2 ms across cross-Atlantic links. When partition tolerance is challenged, "
                "HydraKV guarantees linearizable reads and sequential consistency for concurrent multi-key transactions."
            ),
            metadata={"system": "HydraKV", "conference": "OSDI 2024"},
        ),
        Document(
            id="doc_cs_02",
            title="HydraKV Fault Recovery and Compaction Architecture",
            domain="systems",
            text=(
                "HydraKV uses an append-only LSM-tree storage engine with tiered leveling compaction. In crash recovery "
                "benchmarks on NVMe arrays, node recovery times averaged 3.2 seconds for a 500 GB partition state. Node failure "
                "detection utilizes heartbeats calibrated with a 450 ms timeout threshold, triggering leader election within "
                "an average of 620 ms."
            ),
            metadata={"system": "HydraKV", "topic": "Crash Recovery"},
        ),

        # Adversarial Pair 1: Conflicting Reports on Product Launch & Sales (Temporal / Source Conflict)
        Document(
            id="doc_conflict_a",
            title="NovaDrive Autonomous Vehicle Fleet Launch - Press Release (Q1)",
            domain="autonomous_vehicles",
            text=(
                "NovaDrive formally launched its commercial Level 4 robotaxi service in Phoenix, Arizona in January 2024, "
                "deploying an initial fleet of 250 fully autonomous electric vehicles operating 24 hours a day without safety drivers. "
                "The fleet completed over 100,000 passenger trips in its first 90 days with zero reported safety incidents."
            ),
            metadata={"version": "early_report", "source": "NovaDrive PR"},
        ),
        Document(
            id="doc_conflict_b",
            title="State Transportation Safety Board Audit on NovaDrive - Official Report (Q3)",
            domain="autonomous_vehicles",
            text=(
                "The Arizona Transportation Safety Board safety audit concluded that NovaDrive had deployed only 85 active "
                "vehicles in Phoenix as of April 2024, and mandated that all vehicles maintain licensed backup safety operators "
                "behind the wheel following two non-fatal intersection collisions in February 2024. The 24-hour unsupervised "
                "permit was suspended indefinitely."
            ),
            metadata={"version": "safety_audit", "source": "Arizona Safety Board"},
        ),
    ]

    # 2. Benchmark Queries (Standard, Adversarial Unanswerable, Conflicting Context)
    benchmark_items = [
        # Item 1: Standard Finance
        BenchmarkItem(
            id="bench_001",
            domain="finance",
            question="What was ApexCloud's Q3 2024 gross margin, and what drove the margin expansion?",
            gold_answer=(
                "ApexCloud's non-GAAP gross margin was 78.2%, expanding by 180 basis points. "
                "This margin expansion was driven by custom ASIC silicon deployment across edge datacenters."
            ),
            gold_evidence_spans=[
                GoldEvidence(
                    doc_id="doc_fin_01",
                    span="Non-GAAP gross margin expanded by 180 basis points to 78.2%, driven by custom ASIC silicon deployment across edge datacenters.",
                )
            ],
            gold_atomic_claims=[
                GoldClaim(claim="ApexCloud Q3 2024 gross margin was 78.2%", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_fin_01"]),
                GoldClaim(claim="Gross margin expanded by 180 basis points", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_fin_01"]),
                GoldClaim(claim="Margin expansion was driven by custom ASIC silicon deployment", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_fin_01"]),
            ],
            test_type=TestType.STANDARD,
            expected_abstention=False,
        ),
        
        # Item 2: Standard Biomedical
        BenchmarkItem(
            id="bench_002",
            domain="biomedical",
            question="What was the median progression-free survival and objective response rate for Veloceptin plus nivolumab?",
            gold_answer=(
                "In the Phase 3 RADIANT-4 trial, Veloceptin combined with nivolumab demonstrated a median progression-free "
                "survival (PFS) of 14.8 months and a confirmed objective response rate (ORR) of 58.4%."
            ),
            gold_evidence_spans=[
                GoldEvidence(
                    doc_id="doc_bio_01",
                    span="Veloceptin combined with nivolumab demonstrated a median progression-free survival (PFS) of 14.8 months versus 8.2 months with nivolumab monotherapy... The confirmed objective response rate (ORR) was 58.4%",
                )
            ],
            gold_atomic_claims=[
                GoldClaim(claim="Median progression-free survival was 14.8 months", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_bio_01"]),
                GoldClaim(claim="Objective response rate was 58.4%", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_bio_01"]),
                GoldClaim(claim="Trial was the Phase 3 RADIANT-4 trial", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_bio_01"]),
            ],
            test_type=TestType.STANDARD,
            expected_abstention=False,
        ),

        # Item 3: Standard Systems Latency
        BenchmarkItem(
            id="bench_003",
            domain="systems",
            question="What are the median and 99th percentile read latencies of HydraKV, and how are local reads serviced?",
            gold_answer=(
                "HydraKV achieved a median read latency of 1.4 ms and a 99th percentile read latency of 4.8 ms. "
                "Reads are serviced locally via monotonic read lease grants."
            ),
            gold_evidence_spans=[
                GoldEvidence(
                    doc_id="doc_cs_01",
                    span="HydraKV achieved a median read latency of 1.4 ms and a 99th percentile (p99) read latency of 4.8 ms by servicing reads locally via monotonic read lease grants.",
                )
            ],
            gold_atomic_claims=[
                GoldClaim(claim="Median read latency of HydraKV is 1.4 ms", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_cs_01"]),
                GoldClaim(claim="p99 read latency of HydraKV is 4.8 ms", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_cs_01"]),
                GoldClaim(claim="Reads are serviced locally via monotonic read lease grants", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_cs_01"]),
            ],
            test_type=TestType.STANDARD,
            expected_abstention=False,
        ),

        # Item 4: Adversarial - Unanswerable Query 1 (High lexical overlap, missing fact)
        BenchmarkItem(
            id="bench_004_unanswerable",
            domain="finance",
            question="What specific percentage of ApexCloud's Q3 2024 revenue came from Japanese enterprise clients?",
            gold_answer=None,
            gold_evidence_spans=[],
            gold_atomic_claims=[],
            test_type=TestType.UNANSWERABLE,
            expected_abstention=True,
            metadata={"adversarial_reason": "ApexCloud reports total revenue and EMEA budget scrutiny, but Japanese revenue split is never mentioned."},
        ),

        # Item 5: Adversarial - Unanswerable Query 2
        BenchmarkItem(
            id="bench_005_unanswerable",
            domain="biomedical",
            question="What was the overall 5-year survival rate of pediatric patients treated with Veloceptin?",
            gold_answer=None,
            gold_evidence_spans=[],
            gold_atomic_claims=[],
            test_type=TestType.UNANSWERABLE,
            expected_abstention=True,
            metadata={"adversarial_reason": "The trial only evaluates adult metastatic melanoma progression-free survival (14.8 months); 5-year pediatric data does not exist."},
        ),

        # Item 6: Adversarial - Conflicting Context
        BenchmarkItem(
            id="bench_006_conflicting",
            domain="autonomous_vehicles",
            question="Did NovaDrive operate its Phoenix robotaxi fleet without safety drivers?",
            gold_answer=(
                "There is conflicting evidence in the sources: NovaDrive's press release claims they operated 250 fully autonomous "
                "vehicles 24/7 without safety drivers, whereas the State Transportation Safety Board audit states backup safety "
                "operators were mandated behind the wheel after collisions and only 85 vehicles were active."
            ),
            gold_evidence_spans=[
                GoldEvidence(doc_id="doc_conflict_a", span="deploying an initial fleet of 250 fully autonomous electric vehicles operating 24 hours a day without safety drivers."),
                GoldEvidence(doc_id="doc_conflict_b", span="mandated that all vehicles maintain licensed backup safety operators behind the wheel following two non-fatal intersection collisions"),
            ],
            gold_atomic_claims=[
                GoldClaim(claim="NovaDrive PR claimed 250 vehicles operated without safety drivers", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_conflict_a"]),
                GoldClaim(claim="State Safety Board mandated licensed backup safety operators behind the wheel", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_conflict_b"]),
            ],
            test_type=TestType.CONFLICTING,
            expected_abstention=False,
            metadata={"conflict_docs": ["doc_conflict_a", "doc_conflict_b"]},
        ),

        # Item 7: Multi-Hop Systems
        BenchmarkItem(
            id="bench_007",
            domain="systems",
            question="What is the crash recovery time of HydraKV, and what is its heartbeat failure detection threshold?",
            gold_answer=(
                "HydraKV's node recovery time averaged 3.2 seconds for a 500 GB partition state, and its failure detection "
                "uses heartbeats calibrated with a 450 ms timeout threshold."
            ),
            gold_evidence_spans=[
                GoldEvidence(
                    doc_id="doc_cs_02",
                    span="node recovery times averaged 3.2 seconds for a 500 GB partition state. Node failure detection utilizes heartbeats calibrated with a 450 ms timeout threshold",
                )
            ],
            gold_atomic_claims=[
                GoldClaim(claim="Node recovery times averaged 3.2 seconds for 500 GB partition", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_cs_02"]),
                GoldClaim(claim="Heartbeat failure detection has a 450 ms timeout threshold", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_cs_02"]),
            ],
            test_type=TestType.STANDARD,
            expected_abstention=False,
        ),

        # Item 8: Debt & Repurchase Finance
        BenchmarkItem(
            id="bench_008",
            domain="finance",
            question="How much senior unsecured debt does ApexCloud hold, when does it mature, and what was the share repurchase in August 2024?",
            gold_answer=(
                "ApexCloud holds $1.20 billion in total senior unsecured notes maturing in October 2029 with a 3.875% coupon rate. "
                "In August 2024, the company repurchased $150 million of Class A common stock."
            ),
            gold_evidence_spans=[
                GoldEvidence(
                    doc_id="doc_fin_02",
                    span="total senior unsecured notes of $1.20 billion maturing in October 2029... repurchased $150 million in Class A common stock under its existing $500 million share repurchase authorization.",
                )
            ],
            gold_atomic_claims=[
                GoldClaim(claim="ApexCloud holds $1.20 billion in senior unsecured notes", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_fin_02"]),
                GoldClaim(claim="Senior notes mature in October 2029", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_fin_02"]),
                GoldClaim(claim="ApexCloud repurchased $150 million in common stock in August 2024", status=VerificationLabel.SUPPORTED, gold_doc_ids=["doc_fin_02"]),
            ],
            test_type=TestType.STANDARD,
            expected_abstention=False,
        ),
    ]

    return documents, benchmark_items


def save_benchmark_data(data_dir: str = "data") -> None:
    """Saves the default benchmark dataset and documents into the target directory."""
    raw_dir = os.path.join(data_dir, "raw")
    gold_dir = os.path.join(data_dir, "gold")
    adv_dir = os.path.join(data_dir, "adversarial")
    
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(gold_dir, exist_ok=True)
    os.makedirs(adv_dir, exist_ok=True)

    docs, items = create_synthetic_benchmark()

    # Save documents
    docs_path = os.path.join(raw_dir, "corpus.json")
    with open(docs_path, "w", encoding="utf-8") as f:
        json.dump([doc.model_dump() for doc in docs], f, indent=2)

    # Save standard & adversarial items
    standard_items = [item.model_dump() for item in items if item.test_type == TestType.STANDARD]
    adversarial_items = [item.model_dump() for item in items if item.test_type in (TestType.UNANSWERABLE, TestType.CONFLICTING, TestType.DISTRACTOR)]
    all_items = [item.model_dump() for item in items]

    with open(os.path.join(gold_dir, "benchmark_all.json"), "w", encoding="utf-8") as f:
        json.dump(all_items, f, indent=2)

    with open(os.path.join(gold_dir, "benchmark_standard.json"), "w", encoding="utf-8") as f:
        json.dump(standard_items, f, indent=2)

    with open(os.path.join(adv_dir, "benchmark_adversarial.json"), "w", encoding="utf-8") as f:
        json.dump(adversarial_items, f, indent=2)


if __name__ == "__main__":
    save_benchmark_data("data")
    print("Saved benchmark datasets to data/")
