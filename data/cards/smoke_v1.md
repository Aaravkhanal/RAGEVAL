# Data card — smoke_v1

| Field | Value |
| --- | --- |
| Dataset id | `smoke_v1` |
| Version | `1.0.0` |
| License | `original-synthetic-in-repo` on every document |
| Provenance | Author-written synthetic documents in `rageval/dataset/generator.py` |
| Size | 8 documents, ~527 whitespace tokens; 8 questions (5 standard, 2 unanswerable, 1 conflicting) |
| Domains | Fictional finance, biomedical, systems, and autonomous-vehicle prose |
| Split | Entire set is `smoke`. There is no hidden test split. |
| Gold | Human-authored (single author) gold answers, evidence spans, and claims |
| Not | SEC filings, NEJM articles, or OSDI papers |

Use this set for unit tests, demos, and pipeline smoke runs. Do not report it as a multi-domain scientific benchmark of real sources.
