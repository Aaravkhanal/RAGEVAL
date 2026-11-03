"""Opt-in live workflow check; creates explicitly named test records and a smoke job."""
import json
import os
import time
import tempfile
from pathlib import Path
import httpx
from scripts.restore_remote_artifacts import restore


def run(base):
    headers={'X-RAGEVAL-API-TOKEN':os.environ['RAGEVAL_PUBLIC_TOKEN'],'X-RAGEVAL-ADMIN-TOKEN':os.environ['RAGEVAL_ADMIN_TOKEN']}
    if os.environ.get('RAGEVAL_TEST_SESSION'):
        headers['Authorization']='Bearer '+os.environ['RAGEVAL_TEST_SESSION']
    with httpx.Client(base_url=base,headers=headers,timeout=30) as client:
        def call(method,path,**kwargs):
            response=client.request(method,path,**kwargs)
            response.raise_for_status()
            return response.json()
        assert call('GET','/ready')['status'] in ('ok','ready')
        suffix=str(time.time_ns())
        dataset=call('POST','/workspace/datasets',json={'name':'E2E test '+suffix,'documents':[{'id':'d','text':'Revenue was $100 million.'}],'questions':[{'id':'q','question':'What was revenue?','reference_answer':'$100 million','source_ids':['d']}]})
        key=dataset['id']
        assert any(d['id']==key for d in call('GET','/workspace/datasets')['datasets'])
        captured=call('POST','/workspace/traces',json={'question':'What was revenue?','answer':'Revenue was $100 million [1].','context_chunks':['Revenue was $100 million.'],'configuration':'e2e','dataset_id':key,'question_id':'q','latency_ms':1})
        assert captured['evaluation']['faithfulness_score']==1
        assert any(c['dataset_id']==key for c in call('GET','/workspace/comparison')['configurations'])
        job=call('POST','/experiments',json={'config':'smoke','max_items':2})
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            state=call('GET','/experiments/'+job['id'])['status']['state']
            if state=='complete': break
            if state=='failed': raise RuntimeError('Smoke job failed')
            time.sleep(2)
        else: raise TimeoutError('Smoke job did not finish')
        result=call('GET','/experiments/'+job['id']+'/results')
        assert result['table']
        artifacts=call('GET','/experiments/'+job['id']+'/artifacts')
        with tempfile.TemporaryDirectory() as folder:
            restore(artifacts,Path(folder)/'restored')
            assert (Path(folder)/'restored/metrics.json').exists()
        return {'dataset_id':key,'run_id':job['id'],'checks':'upload, read, capture, comparison, queue, results, artifact restore passed'}

if __name__=='__main__':
    print(json.dumps(run(os.environ.get('RAGEVAL_BASE_URL','http://127.0.0.1:8000')),indent=2))
