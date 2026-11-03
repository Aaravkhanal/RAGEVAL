import pytest
from fastapi.testclient import TestClient
from rageval.server.app import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('RAGEVAL_WORKSPACE_DB', str(tmp_path/'workspace.db'))
    monkeypatch.setenv('RAGEVAL_ADMIN_TOKEN', 'admin')
    monkeypatch.setenv('RAGEVAL_REQUIRE_AUTH', '0')
    monkeypatch.delenv('RAGEVAL_SUPABASE_URL', raising=False)
    return TestClient(app)

HEADERS = {'X-RAGEVAL-ADMIN-TOKEN':'admin'}
DATASET = {'name':'test','documents':[{'id':'d','text':'Revenue was $100 million.'}], 'questions':[{'id':'q','question':'Revenue?', 'reference_answer':'$100 million','source_ids':['d']}]}

def test_dataset_validation_and_restart(client):
    assert client.post('/workspace/datasets',json=DATASET).status_code == 403
    bad = {**DATASET,'questions':[{**DATASET['questions'][0],'source_ids':['missing']}]}
    assert client.post('/workspace/datasets',json=bad,headers=HEADERS).status_code == 422
    created = client.post('/workspace/datasets',json=DATASET,headers=HEADERS)
    assert created.status_code == 201
    with TestClient(app) as restarted:
        assert restarted.get('/workspace/datasets').json()['datasets'][0]['id'] == created.json()['id']

def test_accuracy_reports_missed_contradictions(client):
    response = client.post('/workspace/accuracy',json={'claims':[{'claim':'Revenue was $100 million.','evidence':'Revenue was $100 million.','human_label':'contradicted'}]})
    assert response.status_code == 200, response.text
    report = response.json()
    assert report['accuracy'] == 0
    assert report['per_label']['contradicted']['false_negatives'] == 1
    assert report['per_label']['supported']['false_positives'] == 1

def test_trace_cost_unknown_and_comparison(client):
    row = {'question':'Revenue?', 'answer':'Revenue was $100 million [1].','context_chunks':['Revenue was $100 million.'],'configuration':'baseline','dataset_id':'revenue','question_id':'q','latency_ms':25}
    response = client.post('/workspace/traces',json=row,headers=HEADERS)
    assert response.status_code == 201, response.text
    result = client.get('/workspace/comparison').json()['configurations'][0]
    assert result['mean_cost_usd'] is None
    assert result['mean_latency_ms'] == 25
    assert result['mean_claim_support'] == 1

def test_matched_comparison_ignores_unmatched_questions(client):
    row = {'question':'Revenue?', 'answer':'Revenue was $100 million.','context_chunks':['Revenue was $100 million.'],'configuration':'baseline','dataset_id':'revenue','question_id':'q','latency_ms':25,'cost_usd':0.1}
    assert client.post('/workspace/traces',json=row,headers=HEADERS).status_code == 201
    assert client.post('/workspace/traces',json={**row,'configuration':'candidate','latency_ms':15,'cost_usd':0.05},headers=HEADERS).status_code == 201
    assert client.post('/workspace/traces',json={**row,'configuration':'candidate','question_id':'extra','latency_ms':999},headers=HEADERS).status_code == 201
    delta = client.get('/workspace/comparison?baseline=baseline').json()['paired_deltas'][0]
    assert delta['paired_questions'] == 1
    assert delta['latency_ms_delta'] == -10
    assert delta['cost_usd_delta'] == pytest.approx(-0.05)

def test_remote_failure_never_falls_back_to_local(client, monkeypatch):
    from urllib.error import URLError
    def unavailable(*args, **kwargs):
        raise URLError('offline')
    monkeypatch.setenv('RAGEVAL_SUPABASE_URL','https://example.supabase.co')
    monkeypatch.setenv('RAGEVAL_SUPABASE_KEY','private')
    monkeypatch.setattr('urllib.request.urlopen',unavailable)
    response = client.post('/workspace/datasets',json=DATASET,headers=HEADERS)
    assert response.status_code == 503
    monkeypatch.delenv('RAGEVAL_SUPABASE_URL')
    assert client.get('/workspace/datasets').json()['datasets'] == []

def test_accounts_isolate_datasets_and_block_cross_owner_execution(client, monkeypatch):
    monkeypatch.setenv('RAGEVAL_WORKSPACE_USER_AUTH','1')
    monkeypatch.setenv('RAGEVAL_REQUIRE_AUTH','1')
    monkeypatch.setenv('RAGEVAL_PUBLIC_TOKEN','public')
    monkeypatch.setattr('rageval.server.accounts.auth_request',lambda path,body=None,token=None: {'id':token})
    a={'Authorization':'Bearer user-a'}
    b={'Authorization':'Bearer user-b'}
    created=client.post('/workspace/datasets',json=DATASET,headers=a)
    assert created.status_code==201, created.text
    key=created.json()['id']
    assert client.get('/workspace/datasets',headers=b).json()['datasets']==[]
    assert len(client.get('/workspace/datasets',headers=a).json()['datasets'])==1
    assert client.get('/workspace/datasets',headers={'X-RAGEVAL-API-TOKEN':'public'}).status_code==401
    assert client.post('/workspace/execute',headers=b,json={'dataset_id':key,'configuration':'x','answers':[{'question_id':'q','answer':'$100 million'}]}).status_code==404
    response=client.post('/workspace/execute',headers=a,json={'dataset_id':key,'configuration':'x','answers':[{'question_id':'q','answer':'Revenue was $100 million [1].'}]})
    assert response.status_code==200, response.text
    assert response.json()['n']==1
