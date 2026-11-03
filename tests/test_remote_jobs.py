from rageval.server import remote_jobs


def test_worker_archives_every_artifact_and_finishes_lease(tmp_path, monkeypatch):
    calls=[]
    job={'id':'test-run','lease_token':'lease','config':'smoke','max_items':2}
    def rpc(name,body):
        calls.append((name,body))
        return job if name=='rageval_claim' else None
    monkeypatch.setattr(remote_jobs,'rpc',rpc)
    monkeypatch.setattr('rageval.benchmark.experiments.load_experiment',lambda path:None)
    def run(*args,**kwargs):
        from pathlib import Path
        Path(kwargs['existing_run_dir'],'predictions.jsonl').write_text('{"answer":"test"}\n')
        Path(kwargs['existing_run_dir'],'metrics.json').write_text('{"by_config":{}}')
    monkeypatch.setattr('rageval.benchmark.experiments.run_experiment',run)
    assert remote_jobs.execute(str(tmp_path),'data')
    payload=next(body for name,body in calls if name=='rageval_finish')
    assert payload['lease']=='lease'
    assert payload['final_state']=='complete'
    assert 'predictions.jsonl' in payload['result_body']['files']


def test_empty_queue_does_no_work(monkeypatch):
    monkeypatch.setattr(remote_jobs,'rpc',lambda *args:None)
    assert not remote_jobs.execute('unused','unused')
