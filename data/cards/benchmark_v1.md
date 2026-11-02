# Data card — benchmark_v1

| Field | Value |
| --- | --- |
| Dataset id | `benchmark_v1` |
| Version | `1.4.0` |
| Size | 36 documents, 47 questions (39 dev / 8 test) |
| License mix | U.S. government works (17 U.S.C. § 105, public domain) and original fiction (CC-BY-4.0) |
| Retrieved | 2026-10-28 (v1.0–v1.1 docs); 2026-10-29 (USGS / NASA ISS); 2026-10-30 (v1.3 CDC/NPS/NASA); 2026-11-02 (v1.4 NPS/CDC/NASA) |
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
- CDC About Measles — https://www.cdc.gov/measles/about/index.html (page date 2026-04-29)
- NPS Grand Canyon Nature — https://www.nps.gov/grca/learn/nature/index.htm (last updated 2026-05-07)
- NPS Yosemite Nature — https://www.nps.gov/yose/learn/nature/index.htm (last updated 2023-08-21)
- NASA Science Voyager — https://science.nasa.gov/mission/voyager/ (fetched 2026-10-30)
- NASA Science Hubble — https://science.nasa.gov/mission/hubble/ (fetched 2026-10-30)
- NASA Science Webb — https://science.nasa.gov/mission/webb/ (fetched 2026-10-30)
- CDC About Handwashing — https://www.cdc.gov/clean-hands/about/index.html (page date 2024-02-16)
- NPS Everglades Nature — https://www.nps.gov/ever/learn/nature/index.htm (last updated 2025-04-29)
- NPS Zion Nature — https://www.nps.gov/zion/learn/nature/index.htm (last updated 2026-03-19)
- NPS Acadia Nature — https://www.nps.gov/acad/learn/nature/index.htm (last updated 2026-07-29)
- NPS Great Smoky Mountains Nature — https://www.nps.gov/grsm/learn/nature/index.htm (last updated 2022-12-22)
- CDC About Tetanus — https://www.cdc.gov/tetanus/about/index.html (page date 2026-09-08)
- CDC About Whooping Cough — https://www.cdc.gov/pertussis/about/index.html (page date 2026-06-24)
- NPS Olympic Nature — https://www.nps.gov/olym/learn/nature/index.htm (last updated 2022-10-17)
- NASA Science Parker Solar Probe — https://science.nasa.gov/mission/parker-solar-probe/ (fetched 2026-11-02)

NASA curly quotes were stored as ASCII. Wildlife counts are the NPS Nature-page species list (`67 mammals, 285 birds, …`).

## Original fiction (CC-BY-4.0)

HarborNet, LumenGrid, Nerexin, CedarRail, Millford Public Library, the HarborNet restatement, and the instruction-like document are author-written. They are not real companies, drugs, or agencies.

## Item mix

- 14 original standard fully supported plus v1.2–v1.3 supported items (v1_007 is also the control of pair `pair_harbornet_q2`; v1_029 last volcanism; v1_031 ISS 25-year mark; v1_033–v1_040 except v1_034)
- 5 unanswerable (adds v1_032 Expedition 75 Thanksgiving dinner)
- 3 conflicting (CedarRail ×2 plus HarborNet pair `v1_028`)
- 4 mixed-support (RQ3): gold answer is fully supported; `metadata.example_mixed_answer` appends an unsupported or contradicted claim that keeps token F1 high
- 2 lexical distractor questions whose gold lives in a small subset of the corpus
- 3 numerical/negation (`v1_025` CDC influenza D “not known to cause”; `v1_030` USGS ~80 post-caldera eruptions; `v1_034` Grand Canyon acres/depth)
- 1 empty-context protocol (`v1_026`; retrieval is dropped before generation)
- 1 instruction-like document (`v1_027`; injection text tells the assistant to answer 99.0% churn)

Test remains 8 held-out ids from v1.0.0. New v1.1.0–v1.4.0 items are **dev**. The **published** ablation in `reports/` is v1.0.0 n=24 (`20261028T183042Z_a97ad68f`). Companion mock+NLI scores: 1.1.0 `20261029T165024Z_657c8089` (`reports/phase7/v1_1_matrix/`) and 1.2.0 `20261029T173408Z_de870a29` (`reports/phase7/v1_2_matrix/`, includes `v1_029`–`v1_032`). v1.3.0/1.4.0 have no recorded NLI companion yet. The `independent` split keeps one item per unused gold document (`items_independent.json`, n=30, `H_independent.yaml`). n=30 meets the count threshold with disjoint gold documents; labels remain single-author, so this is not a confirmatory ranking. The full 47-item set still shares documents.

Use `smoke_v1` for CI. Use `benchmark_v1` for the licensed pilot. Do not treat n=47 as a confirmatory scientific result. HTTP jobs cap `max_items` at 32; the CLI can run all 47.
