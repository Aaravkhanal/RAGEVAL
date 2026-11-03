"""Validated user benchmarks, saved evaluations, and human-label accuracy reports."""
from __future__ import annotations
import json
import os
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field, model_validator

def remote(method, query, body=None):
    from urllib.request import Request, urlopen
    from urllib.error import URLError
    base = os.environ['RAGEVAL_SUPABASE_URL'].rstrip('/')
    if not base.startswith('https://'):
        raise HTTPException(503, 'Remote storage requires HTTPS')
    key = os.environ.get('RAGEVAL_SUPABASE_KEY')
    if not key:
        raise HTTPException(503, 'Remote storage key is missing')
    headers = {'apikey': key, 'Content-Type': 'application/json'}
    if not key.startswith('sb_secret_'):
        headers['Authorization'] = 'Bearer ' + key
    request = Request(base + '/rest/v1/rageval_records' + query,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except URLError:
        raise HTTPException(503, 'Remote storage unavailable; no local fallback was used') from None


router = APIRouter(prefix='/workspace', tags=['workspace'])


def connection():
    path = Path(os.environ.get('RAGEVAL_WORKSPACE_DB', 'experiments/workspace.sqlite3'))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL)')
    return conn


def save(kind, body):
    key = uuid.uuid4().hex
    if os.environ.get('RAGEVAL_SUPABASE_URL'):
        remote('POST', '', {'id': key, 'kind': kind, 'body': body})
        return {'id': key, **body}
    with closing(connection()) as conn, conn:
        conn.execute('INSERT INTO records VALUES (?, ?, ?)', (key, kind, json.dumps(body)))
    return {'id': key, **body}


def records(kind):
    if os.environ.get('RAGEVAL_SUPABASE_URL'):
        return [{'id': row['id'], **row['body']} for row in remote('GET', '?select=id,body&kind=eq.' + kind + '&order=created_at.desc&limit=200')]
    with closing(connection()) as conn, conn:
        return [{'id': key, **json.loads(body)} for key, body in conn.execute('SELECT id, body FROM records WHERE kind=? ORDER BY rowid DESC LIMIT 200', (kind,))]


def admin(token):
    import hmac
    expected = os.environ.get('RAGEVAL_ADMIN_TOKEN')
    if not expected or not token or not hmac.compare_digest(token, expected):
        raise HTTPException(403, 'A valid admin token is required to save workspace data')


class Source(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=8192)


class Question(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=2048)
    reference_answer: str | None = Field(default=None, max_length=16384)
    source_ids: list[str] = Field(min_length=1, max_length=10)
    expected_abstention: bool = False


class Dataset(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    documents: list[Source] = Field(min_length=1, max_length=100)
    questions: list[Question] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def validate_links(self):
        ids = {d.id for d in self.documents}
        if len(ids) != len(self.documents) or len({q.id for q in self.questions}) != len(self.questions):
            raise ValueError('Document and question IDs must be unique')
        for q in self.questions:
            if not set(q.source_ids) <= ids:
                raise ValueError(f'Unknown source ID in question {q.id}')
            if q.reference_answer is None and not q.expected_abstention:
                raise ValueError('Each question needs a reference_answer or expected_abstention=true')
        return self


@router.get('/storage')
def storage():
    return {'remote_configured': bool(os.environ.get('RAGEVAL_SUPABASE_URL')), 'backend': 'supabase' if os.environ.get('RAGEVAL_SUPABASE_URL') else 'sqlite', 'durable_storage_configured': bool(os.environ.get('RAGEVAL_WORKSPACE_DB')), 'note': 'Durability requires RAGEVAL_WORKSPACE_DB on a persistent volume. Render free local storage is ephemeral.'}


@router.post('/datasets', status_code=201)
def upload_dataset(dataset: Dataset, x_rageval_admin_token: str | None = Header(default=None)):
    admin(x_rageval_admin_token)
    return save('dataset', dataset.model_dump())


@router.get('/datasets')
def datasets():
    return {'datasets': records('dataset')}


class Trace(BaseModel):
    question: str = Field(min_length=1, max_length=2048)
    answer: str = Field(min_length=1, max_length=16384)
    context_chunks: list[str] = Field(min_length=1, max_length=10)
    configuration: str = Field(default='external', min_length=1, max_length=100)
    dataset_id: str = Field(min_length=1, max_length=100)
    question_id: str = Field(min_length=1, max_length=100)
    latency_ms: float = Field(ge=0, allow_inf_nan=False)
    cost_usd: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @model_validator(mode='after')
    def bound_sources(self):
        if any(not c.strip() or len(c) > 8192 for c in self.context_chunks):
            raise ValueError('Source passages must contain 1–8192 characters')
        return self


@router.post('/traces', status_code=201)
def trace(row: Trace, x_rageval_admin_token: str | None = Header(default=None)):
    admin(x_rageval_admin_token)
    from rageval.server.app import LiveEvaluationRequest, evaluate_answer
    result = evaluate_answer(LiveEvaluationRequest(question=row.question, answer=row.answer, context_chunks=row.context_chunks))
    return save('trace', {**row.model_dump(), 'evaluation': result.evaluation.model_dump(mode='json')})


@router.get('/archived-runs')
def archived_runs():
    return {'runs': records('run')}


@router.get('/traces')
def traces():
    return {'traces': records('trace')}


@router.get('/comparison')
def comparison(baseline: str | None = None):
    from collections import defaultdict
    groups = defaultdict(list)
    for row in records('trace'):
        groups[(row['dataset_id'], row['configuration'])].append(row)
    output = []
    for (dataset, config), rows in groups.items():
        n = len(rows)
        known_costs = [r['cost_usd'] for r in rows if r['cost_usd'] is not None]
        output.append({'dataset_id': dataset, 'configuration': config, 'n': n,
            'question_ids': sorted({r['question_id'] for r in rows}),
            'mean_claim_support': sum(r['evaluation']['faithfulness_score'] for r in rows)/n,
            'mean_latency_ms': sum(r['latency_ms'] for r in rows)/n,
            'mean_cost_usd': sum(known_costs)/n if len(known_costs) == n else None})
    deltas = []
    if baseline:
        for (dataset, config), rows in groups.items():
            base = groups.get((dataset, baseline), [])
            if config == baseline or not base:
                continue
            # Require exactly one observation for each shared question; repeated
            # captures must not silently change the weight of a question.
            ids = {r['question_id'] for r in rows} & {r['question_id'] for r in base}
            paired = [(next(r for r in rows if r['question_id']==q), next(r for r in base if r['question_id']==q)) for q in sorted(ids)
                if sum(r['question_id']==q for r in rows)==1 and sum(r['question_id']==q for r in base)==1]
            if not paired:
                continue
            n = len(paired)
            deltas.append({'dataset_id': dataset, 'configuration': config, 'baseline': baseline, 'paired_questions': n,
                'claim_support_delta': sum(a['evaluation']['faithfulness_score']-b['evaluation']['faithfulness_score'] for a,b in paired)/n,
                'latency_ms_delta': sum(a['latency_ms']-b['latency_ms'] for a,b in paired)/n,
                'cost_usd_delta': sum(a['cost_usd']-b['cost_usd'] for a,b in paired)/n if all(a['cost_usd'] is not None and b['cost_usd'] is not None for a,b in paired) else None})
    return {'paired_deltas': deltas, 'configurations': output, 'note': 'Compare only identical datasets and question sets. Claim support is heuristic, not human accuracy. Unknown cost stays null.'}


class LabeledClaim(BaseModel):
    claim: str = Field(min_length=1, max_length=2048)
    evidence: str = Field(min_length=1, max_length=8192)
    human_label: Literal['supported', 'partially_supported', 'unsupported', 'contradicted', 'ambiguous']


class AccuracyRequest(BaseModel):
    claims: list[LabeledClaim] = Field(min_length=1, max_length=100)


@router.post('/accuracy')
def accuracy(request: AccuracyRequest):
    from rageval.server.runtime import get_evaluator
    verifier = get_evaluator('heuristic').nli_verifier
    labels = ['supported', 'partially_supported', 'unsupported', 'contradicted', 'ambiguous']
    matrix = {gold: {pred: 0 for pred in labels} for gold in labels}
    errors = []
    for row in request.claims:
        from rageval.core.schemas import AtomicClaim
        from rageval.integrations.external import chunks_from_contexts
        predicted = verifier.verify_claim(AtomicClaim(claim_id='human', text=row.claim, raw_sentence=row.claim), chunks_from_contexts([row.evidence])).label.value
        matrix[row.human_label][predicted] += 1
        if predicted != row.human_label:
            errors.append({**row.model_dump(), 'predicted': predicted})
    metrics = {}
    for label in labels:
        tp = matrix[label][label]
        fp = sum(matrix[g][label] for g in labels if g != label)
        fn = sum(matrix[label][p] for p in labels if p != label)
        metrics[label] = {'precision': tp/(tp+fp) if tp+fp else None, 'recall': tp/(tp+fn) if tp+fn else None, 'false_positives': fp, 'false_negatives': fn}
    return {'n': len(request.claims), 'accuracy': sum(matrix[l][l] for l in labels)/len(request.claims), 'confusion_matrix': matrix, 'per_label': metrics, 'errors': errors, 'method': 'heuristic', 'note': 'Human labels are supplied by the caller; their independence is not verified.'}
