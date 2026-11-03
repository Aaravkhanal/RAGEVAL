"""Leased Supabase queue and complete run artifacts for ephemeral workers."""
import base64
import os
import threading
from pathlib import Path
from rageval.server.workspace import remote


def enabled():
    return os.environ.get('RAGEVAL_REMOTE_JOBS') == '1'


def rpc(name, body):
    return remote('POST', '', body, resource='rpc/'+name)


def enqueue(run_id, config, max_items):
    rpc('rageval_enqueue', {'job_id':run_id, 'config_name':config, 'item_limit':max_items})
    return {'id':run_id,'status':'queued','poll':'/experiments/'+run_id,'config':config,'max_items':max_items}


def list_jobs():
    return remote('GET','?select=id,config,state,updated&order=updated.desc&limit=200',resource='rageval_jobs')


def get_job(run_id, include_payload=False):
    from rageval.server.catalog import SAFE_ID
    if not SAFE_ID.fullmatch(run_id):
        raise ValueError('Invalid run ID')
    rows = remote('GET','?select=' + ('*' if include_payload else 'id,config,state,updated') + '&id=eq.'+run_id,resource='rageval_jobs')
    if not rows:
        raise FileNotFoundError(run_id)
    return rows[0]


def execute(output_root, data_root):
    job = rpc('rageval_claim', {})
    if not job:
        return False
    from rageval.benchmark.experiments import load_experiment, run_experiment
    from rageval.server.jobs import resolve_config_path
    from rageval.benchmark.run_store import create_run_dir, write_run_status
    from rageval.server.catalog import get_experiment_results
    run_id, lease = job['id'], job['lease_token']
    run_dir = create_run_dir(output_root,run_id=run_id)
    stopped = threading.Event()
    def heartbeat():
        while not stopped.wait(10):
            try:
                rpc('rageval_heartbeat', {'job_id':run_id,'lease':lease})
            except Exception:
                # Finalization verifies lease ownership; a disconnected worker
                # cannot overwrite results from a later claimant.
                return
    pulse = threading.Thread(target=heartbeat,daemon=True)
    pulse.start()
    try:
        write_run_status(run_dir,'running')
        run_experiment(load_experiment(resolve_config_path(job['config'])),data_dir=data_root,output_root=output_root,max_items=job['max_items'],existing_run_dir=run_dir)
        write_run_status(run_dir,'complete')
        files = {str(p.relative_to(run_dir)):base64.b64encode(p.read_bytes()).decode() for p in Path(run_dir).rglob('*') if p.is_file()}
        result = get_experiment_results(run_id,output_root)
        rpc('rageval_finish', {'job_id':run_id,'lease':lease,'final_state':'complete','result_body':{'result':result,'files':files}})
    except Exception as exc:
        rpc('rageval_finish', {'job_id':run_id,'lease':lease,'final_state':'failed','result_body':{'error':type(exc).__name__}})
    finally:
        stopped.set()
        pulse.join(timeout=1)
    return True
