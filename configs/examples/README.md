# Example inputs

`external_score.jsonl` is a two-row fixture for `rageval score` (question + chunks + answer). It is not a benchmark.

```bash
rageval score --input configs/examples/external_score.jsonl --output /tmp/scores.jsonl --method heuristic
```
