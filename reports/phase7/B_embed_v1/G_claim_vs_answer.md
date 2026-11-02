# RAGeval diagnostic claim-level vs answer-level (mixed-support)

Slice: `scenario_type=mixed_support`. Gold answers are fully supported; token F1 can stay high while claim support is mixed (RQ3).

| Configuration | mixed n | answer F1 | claim support rate |
| --- | ---: | ---: | ---: |
| Embed_MiniLM | 4 | 0.5689 | 0.4583 |
| Embed_MPNet | 4 | 0.5689 | 0.3333 |

No overall score. n on this slice is 4 Dataset version 1.3.0.
