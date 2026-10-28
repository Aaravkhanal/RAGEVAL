# Data card — benchmark_v1

| Field | Value |
| --- | --- |
| Dataset id | `benchmark_v1` |
| Version | `1.0.0` |
| Size | 16 documents, 24 questions (16 dev / 8 test) |
| License mix | U.S. government works (17 U.S.C. § 105, public domain) and original fiction (CC-BY-4.0) |
| Retrieved | 2026-10-28 |
| Annotator | Single author, disclosed |
| Split | Dev `v1_001`–style majority; test is 8 held-out ids. Test was not used to choose metrics or NLI thresholds. The first ablation still reports **all 24** because `n_test=8` is underpowered. |
| Gold | Human-authored questions, answers, verbatim evidence spans, and 5-way claim labels |
| Not | The Niu et al. 2024 RAGTruth corpus; SEC filings; NEJM; Wikipedia |

## Public-domain excerpts

Short passages from:

- NASA Apollo 11 Mission Overview — https://www.nasa.gov/missions/apollo/apollo-11/apollo-11-mission-overview/
- CDC Types of Influenza Viruses — https://www.cdc.gov/flu/about/viruses-types.html (page date 2025-09-26)
- NPS Yellowstone Nature — https://www.nps.gov/yell/learn/nature/index.htm (last updated 2025-04-18)

NASA curly quotes were stored as ASCII. Wildlife counts are the NPS Nature-page species list (`67 mammals, 285 birds, …`).

## Original fiction (CC-BY-4.0)

HarborNet, LumenGrid, Nerexin, CedarRail, and Millford Public Library are author-written. They are not real companies, drugs, or agencies.

## Item mix

- 12 standard fully supported
- 4 unanswerable
- 2 conflicting
- 4 mixed-support (RQ3): gold answer is fully supported; `metadata.example_mixed_answer` appends an unsupported or contradicted claim that keeps token F1 high
- 2 distractor questions whose gold lives in a small subset of the corpus

Use `smoke_v1` for CI. Use `benchmark_v1` for the licensed pilot. Do not treat n=24 as a confirmatory scientific result.
