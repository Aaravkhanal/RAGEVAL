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

## Accounts and private workspaces

The dashboard supports email registration and sign-in through Supabase Auth.
Confirm your email before signing in if confirmation is enabled. Passwords go to
Supabase through the server; sessions are held only in tab memory, not localStorage.
Set RAGEVAL_WORKSPACE_USER_AUTH=1 to require a verified session for workspace
requests. Admin-token holders retain the legacy admin namespace for operations.
Every saved record is stamped with the verified account ID and queries are scoped
to that ID. Callers cannot choose another owner's ID. Existing shared records are
migrated into the admin namespace by the remote_jobs.sql migration.

Admin experiment jobs remain admin-only; they are not exposed as arbitrary
user-submitted execution. Account sessions do not grant experiment admin rights.
This is initial account support, not a complete account lifecycle product: password
reset, account deletion, session refresh UI and organizational sharing need further
work. Expired sessions require signing in again.

## Durable jobs, complete artifacts, and recovery

Apply docs/storage/remote_jobs.sql to the same Supabase project, then enable
RAGEVAL_REMOTE_JOBS=1 in both API and worker (the Render process shares the env).
The worker leases a database job, heartbeats its lease, and archives every run file
as base64 in the job payload. An expired lease can be reclaimed after restart;
stale workers cannot finalize a job claimed by another worker. Database outages
are retried by the worker loop. Run execution is at least once, not exactly once.
The current queue serializes jobs globally for the small free instance.

GET /experiments/{id}/artifacts with both service and admin tokens exports the
complete archive. Restore to a new local directory with:

```
python -m scripts.restore_remote_artifacts exported-artifacts.json restored-run
```

The restore validates paths and base64 before creating the destination. The test
suite includes a restore round trip and rejects path traversal. This is logical
artifact recovery, not a replacement for a database backup. Configure and test
Supabase database backups according to your account's available features; this
repository does not claim that a hosted database disaster recovery drill occurred.

## Execute a custom benchmark

After saving a dataset, upload another JSON file and choose Evaluate dataset answers:

```json
{"dataset_id":"ID returned when saving the dataset","configuration":"my-agent-v1","answers":[{"question_id":"q1","answer":"Revenue was $100 million [1]."}]}
```

The server evaluates up to 20 supplied answers against their linked reference
passages and saves the run. It does not fetch arbitrary agent URLs or execute
uploaded code. This protocol measures generation given reference evidence; use
captured traces when studying errors in actual retrieval. Tables summarize saved
reports; full JSON remains available for inspection/export.

## Monitoring and deployed checks

GET /workspace/operations (admin token required) reports storage readability and
job counts by state. /health remains a liveness check; /ready fails if the queue
storage cannot be reached. GitHub's deployment workflow checks readiness every six
hours. Configure GitHub Actions failure notifications for alerts. The manually
triggered workflow exercises uploads, reads, capture, comparisons, job completion,
artifact export and restore. It requires GitHub secrets RAGEVAL_PUBLIC_TOKEN and
RAGEVAL_ADMIN_TOKEN. It creates named E2E records and a smoke job; it is opt-in.
No external monitoring notification destination has been configured automatically.

For logical application-data backups, `python -m scripts.backup_remote backup
private-backup.json` exports both records and queue/artifacts using the Supabase
URL/key from environment variables. Pause writes for cross-table consistency.
The output is private and is created with owner-only permissions. Restore to a
prepared project with `python -m scripts.backup_remote restore private-backup.json
--confirm-project PROJECT_REF`. This upserts data and requires an exact project
confirmation. Tests cover data round trips and wrong-project rejection using an
isolated transport. A live full-database restore, Auth-user backup, scheduled
protected backup destination and alert recipient remain operational setup tasks.
