# Release diagnostic: claim verification and operational baseline

## Research question

How reliably does the lightweight hosted verifier distinguish supported,
unsupported, partially supported, contradictory, and ambiguous claims?

## Method

Run the commands in reproducibility.json using the repository's hashed Python
lock. The manifest records the source revision and hashes of dataset/configuration
files. The smoke benchmark uses BM25 retrieval, mock generation and a lexical
verifier on eight synthetic smoke questions. It is an operational baseline,
not evidence of generalization to real agents. The separate verifier diagnostic
scores the existing 24-example labeled set, not newly collected independent
human judgments. See verifier_diagnostic.md for class metrics and errors.

## Results

The heuristic verifier achieved macro-F1 0.514 with 10 errors out of 24 examples.
These small-sample results expose limitations; they do not establish production
accuracy. Inspect the per-class confusion matrix rather than extrapolating the
aggregate score to arbitrary domains. The experiment folder contains the fresh
smoke configuration, metrics and predictions.

## Limitations and next evidence

The diagnostic labels are not an independently adjudicated multi-rater study.
The human review queue and agreement tooling exist, but independent people must
complete them. Freeze the reviewed set before tuning thresholds, keep a held-out
test split, report disagreements and Cohen's kappa, and publish false positives
and missed contradictions by scenario. Do not relabel model-generated judgments
as human observations. No billed provider rate was supplied; unknown USD cost
must remain unknown. Timing describes the machine used for this run.

The broader paper and retrieval comparisons remain in reports/paper.tex and
reports/phase8/retrieval_v2.json. This release diagnostic supplements those
artifacts; it does not replace their protocols or turn pilot findings into a
confirmatory result.
