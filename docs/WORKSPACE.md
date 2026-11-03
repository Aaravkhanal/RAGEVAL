# Custom evaluation workspace

Connect the public token. Open **My benchmarks**. Saving datasets and traces also
requires the admin token (enter it on Experiments). Access is shared among token
holders, not isolated by user account. Upload only data appropriate for that scope.

## Human-label accuracy

Download the labels template, replace it with independently reviewed claims and
evidence, and upload it with **Measure accuracy**. Allowed labels are supported,
partially_supported, unsupported, contradicted, ambiguous. Reports include a
confusion matrix, per-label precision/recall, false positives, missed contradictions
(false negatives for contradicted), and individual errors. No measured human
accuracy is claimed until real human judgments are supplied. Template is illustrative.

## Custom datasets

Download the dataset example. Supply unique document/question IDs, document text,
questions, reference answers and source IDs. Unanswerable questions use null
reference_answer and expected_abstention=true. Unknown source IDs and duplicate
IDs are rejected. Upload JSON up to 60 KB through My benchmarks. These saved
benchmarks do not automatically execute an arbitrary agent: use the capture client.

## Capture your agent

```python
import os
from rageval.integrations.client import RAGEvalClient
client = RAGEvalClient('https://rageval-free.onrender.com',
    os.environ['RAGEVAL_PUBLIC_TOKEN'], os.environ['RAGEVAL_ADMIN_TOKEN'])

@client.monitor(configuration='baseline', dataset_id='my-benchmark', question_id='q1')
def agent(question):
    # Return your real agent output and the passages actually retrieved.
    return {'answer': 'Revenue was $100 million [1].',
            'context_chunks': ['Revenue was $100 million.']}

agent('What was revenue?')
```

Both sync and async functions are supported. Capture errors propagate; choose
explicit error handling in your application. The reported latency measures the
agent call, excluding evaluation/network time. Supply cost_usd only when known.
For each benchmark question use its own question_id and repeat across named
configurations. **Compare configurations** reports mean claim support, latency,
and cost grouped by dataset/configuration. Inspect question IDs and sample counts:
only matched questions are comparable. Missing costs remain null. Claim support
is not reference-answer accuracy. Raw saved traces are at GET /workspace/traces.

## Storage across Render restarts

SQLite defaults to local temporary storage on Render Free. A persistent volume can
be selected with RAGEVAL_WORKSPACE_DB; setting a path alone does not provision one.
For external durable storage, create a Supabase project, run
[the schema](storage/supabase.sql), then configure Render environment variables:

- RAGEVAL_SUPABASE_URL: the project's HTTPS URL
- RAGEVAL_SUPABASE_KEY: server-side service-role key

No additional Python package is needed. Remote failures return errors without
silently falling back to temporary storage. New datasets and captured evaluations
are stored remotely. Completed experiment metric reports are archived remotely by
the worker; browse **Archived job results**. Existing local data is not migrated.
The pending job queue and full prediction artifacts remain local; queued jobs may
be lost after restarts. Full queue durability still requires a persistent volume.
Remote setup requires an external account and is not enabled by this code change.
Export reports before restart until durable storage has been configured.
