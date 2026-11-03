"""Logical Supabase data backup/restore using server-side environment credentials.

Contains private records: store exported files in protected backup storage.
Does not export Supabase Auth users or replace a full PostgreSQL backup.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

TABLES = ('rageval_records', 'rageval_jobs')


def request(table, method='GET', body=None, query=''):
    key=os.environ['RAGEVAL_SUPABASE_KEY']
    base=os.environ['RAGEVAL_SUPABASE_URL'].rstrip('/')
    if not base.startswith('https://'):
        raise ValueError('HTTPS required')
    headers={'apikey':key,'Content-Type':'application/json','Prefer':'resolution=merge-duplicates'}
    if not key.startswith('sb_secret_'):
        headers['Authorization']='Bearer '+key
    req=Request(base+'/rest/v1/'+table+query,headers=headers,method=method,data=json.dumps(body).encode() if body is not None else None)
    with urlopen(req,timeout=30) as response:
        data=response.read()
        return json.loads(data) if data else None


def backup():
    tables={}
    for table in TABLES:
        rows=[]
        offset=0
        while True:
            page=request(table,query=f'?select=*&order=id&limit=100&offset={offset}')
            rows.extend(page)
            if len(page)<100: break
            offset+=100
        tables[table]=rows
    return {'schema':'rageval.logical_backup.v1','tables':tables,
        'note':'Pause writes for a consistent cross-table snapshot. Auth users are excluded.'}


def restore(payload, confirm_project):
    from urllib.parse import urlparse
    project=urlparse(os.environ['RAGEVAL_SUPABASE_URL']).hostname.split('.')[0]
    if project!=confirm_project or payload.get('schema')!='rageval.logical_backup.v1':
        raise ValueError('Project confirmation or backup schema mismatch')
    if set(payload['tables'])!=set(TABLES):
        raise ValueError('Unexpected backup tables')
    for table in TABLES:
        rows=payload['tables'][table]
        for offset in range(0,len(rows),100):
            request(table,'POST',rows[offset:offset+100])

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['backup','restore'])
    parser.add_argument('file',type=Path)
    parser.add_argument('--confirm-project')
    args=parser.parse_args()
    if args.action=='backup':
        with args.file.open('x') as out:
            os.chmod(args.file,0o600)
            json.dump(backup(),out)
    else:
        restore(json.loads(args.file.read_text()),args.confirm_project)
