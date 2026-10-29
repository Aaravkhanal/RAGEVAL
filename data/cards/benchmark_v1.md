# Data card — benchmark_v1

| Field | Value |
| --- | --- |
| Dataset id | `benchmark_v1` |
| Version | `1.2.0` |
| Size | 21 documents, 32 questions (24 dev / 8 test) |
| License mix | U.S. government works (17 U.S.C. § 105, public domain) and original fiction (CC-BY-4.0) |
| Retrieved | 2026-10-28 (v1.0–v1.1 docs); 2026-10-29 (USGS / NASA ISS) |
| Annotator | Single author, disclosed |
| Split | Dev `v1_001`–style majority; test is 8 held-out ids. Test was not used to choose metrics or NLI thresholds. The first ablation still reports **all 24** because `n_test=8` is underpowered. |
| Gold | Human-authored questions, answers, verbatim evidence spans, and 5-way claim labels |
| Not | The Niu et al. 2024 RAGTruth corpus; SEC filings; NEJM; Wikipedia |

## Public-domain excerpts

Short passages from:

- NASA Apollo 11 Mission Overview — https://www.nasa.gov/missions/apollo/apollo-11/apollo-11-mission-overview/
- CDC Types of Influenza Viruses — https://www.cdc.gov/flu/about/viruses-types.html (page date 2025-09-26)
- NPS Yellowstone Nature — https://www.nps.gov/yell/learn/nature/index.htm (last updated 2025-04-18)
- USGS FAQ last Yellowstone eruption — https://www.usgs.gov/faqs/when-was-last-time-yellowstone-erupted (updated 2026-07-29)
- USGS FAQ post-caldera eruptions — https://www.usgs.gov/faqs/how-much-volcanic-activity-has-there-been-yellowstone-most-recent-giant-eruption (updated 2026-07-29)
- NASA International Space Station — https://www.nasa.gov/international-space-station/ (fetched 2026-10-29)

NASA curly quotes were stored as ASCII. Wildlife counts are the NPS Nature-page species list (`67 mammals, 285 birds, …`).

## Original fiction (CC-BY-4.0)

HarborNet, LumenGrid, Nerexin, CedarRail, Millford Public Library, the HarborNet restatement, and the instruction-like document are author-written. They are not real companies, drugs, or agencies.

## Item mix

- 14 standard fully supported (v1_007 is also the control of pair `pair_harbornet_q2`; v1_029 last volcanism; v1_031 ISS 25-year mark)
- 5 unanswerable (adds v1_032 Expedition 75 Thanksgiving dinner)
- 3 conflicting (CedarRail ×2 plus HarborNet pair `v1_028`)
- 4 mixed-support (RQ3): gold answer is fully supported; `metadata.example_mixed_answer` appends an unsupported or contradicted claim that keeps token F1 high
- 2 lexical distractor questions whose gold lives in a small subset of the corpus
- 2 numerical/negation (`v1_025` CDC influenza D “not known to cause”; `v1_030` USGS ~80 post-caldera eruptions)
- 1 empty-context protocol (`v1_026`; retrieval is dropped before generation)
- 1 instruction-like document (`v1_027`; injection text tells the assistant to answer 99.0% churn)

Test remains 8 held-out ids from v1.0.0. New v1.1.0 and v1.2.0 items are **dev**. The **published** ablation in `reports/` is v1.0.0 n=24 (`20261028T183042Z_a97ad68f`). Companion mock+NLI scores the 28-item 1.1.0 set: run `20261029T165024Z_657c8089` (`reports/phase7/v1_1_matrix/`). `v1_029`–`v1_032` are **unscored** in that companion. n=32 is still underpowered (confirmatory n≥30 **i.i.d.**; items share documents).

Use `smoke_v1` for CI. Use `benchmark_v1` for the licensed pilot. Do not treat n=32 as a confirmatory scientific result.
