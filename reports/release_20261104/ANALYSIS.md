# Lexical verifier development diagnostic

The previous heuristic made 10 errors on the 24-example verifier diagnostic
(macro-F1 0.5140, accuracy 0.5833). The revised heuristic makes 4 errors
(macro-F1 0.8529, accuracy 0.8333). See verifier_diagnostic.md and its JSON for
class metrics, confusion matrix and remaining errors.

The changes compare numeric assertions within shared relations, handle negation
symmetrically, score mixed clauses as partially supported, normalize plurals, and
avoid assuming that words such as “discontinued” imply a contradiction. Location
qualifiers in a source no longer contradict a shorter compatible location claim.
Unrelated numeric assertions stay unsupported rather than becoming contradictions
merely because they share an entity name.

These changes were developed using the diagnostic failures, so the 24-item set is
now explicitly a development set. The improvement is not a held-out estimate or
independent human validation. Additional regression tests use new entities,
quantities and locations, but are software regression checks, not a human study.
No human judgments have been invented. The verifier still uses lexical rules and
can fail on paraphrases, entity lists, reference resolution and complex evidence.

Reproduce with:

```
python -m rageval.cli verifier-eval --method heuristic --output reports/release_20261104/verifier_diagnostic.md
pytest tests/test_lexical_verifier.py
```

Human-review workflows and the prior independent-rater requirement remain in
place. Use an independently reviewed, frozen test set before claiming deployment
accuracy or a general improvement percentage.
