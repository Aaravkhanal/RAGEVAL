"""Restore all application tables/schema in two disposable local PostgreSQL DBs.

Accepts only localhost/socket PostgreSQL; never runs against the hosted service.
Auth identities and Supabase platform schemas are outside this application backup.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlparse,urlunparse
import uuid


def command(argv, sql=None):
    return subprocess.run(argv,input=sql,text=True,capture_output=True,check=True,env={**os.environ,'PGOPTIONS':'-c timezone=UTC'}).stdout.strip()


def verify(payload):
    url=os.environ.get('RAGEVAL_RESTORE_DATABASE_URL','postgresql://postgres:postgres@localhost:5432/postgres')
    parsed=urlparse(url)
    if parsed.hostname not in ('localhost','127.0.0.1',None): raise ValueError('Restore drills require a disposable local database')
    if payload.get('schema')!='rageval.logical_backup.v1': raise ValueError('Unexpected backup schema')
    names=['rageval_drill_'+uuid.uuid4().hex[:12] for _ in range(2)]
    def database(name): return urlunparse(parsed._replace(path='/'+name))
    root=Path(__file__).resolve().parents[1]
    try:
        command(['psql',url,'-v','ON_ERROR_STOP=1','-c',"DO $$ BEGIN CREATE ROLE anon; EXCEPTION WHEN duplicate_object THEN NULL; END $$; DO $$ BEGIN CREATE ROLE authenticated; EXCEPTION WHEN duplicate_object THEN NULL; END $$; DO $$ BEGIN CREATE ROLE service_role; EXCEPTION WHEN duplicate_object THEN NULL; END $$;"])
        for name in names: command(['createdb','--maintenance-db='+url,name])
        source,target=map(database,names)
        for name in ('supabase.sql','remote_jobs.sql','backups.sql'):
            command(['psql',source,'-v','ON_ERROR_STOP=1'],(root/'docs/storage'/name).read_text())
        for table in ('rageval_records','rageval_jobs'):
            rows=json.dumps(payload['tables'][table]).replace("'","''")
            command(['psql',source,'-v','ON_ERROR_STOP=1'],f"insert into public.{table} select * from jsonb_populate_recordset(null::public.{table},'{rows}'::jsonb);")
        with tempfile.TemporaryDirectory() as folder:
            dump=Path(folder)/'database.dump'
            command(['pg_dump',source,'-Fc','--schema=public','-f',str(dump)])
            command(['pg_restore','--clean','--if-exists','--no-owner','--dbname='+target,str(dump)])
        snapshots=[]
        for db in (source,target):
            snapshots.append(json.loads(command(['psql',db,'-At','-v','ON_ERROR_STOP=1','-c','select public.rageval_snapshot();'])))
        if snapshots[0]['tables']!=snapshots[1]['tables']: raise ValueError('Restored database content mismatch')
        from datetime import datetime, timezone
        def canonical(tables):
            result=json.loads(json.dumps(tables))
            for rows in result.values():
                for row in rows:
                    for key in ('created_at','updated','lease_until'):
                        if row.get(key): row[key]=datetime.fromisoformat(row[key].replace('Z','+00:00')).astimezone(timezone.utc).isoformat()
            return result
        if canonical(snapshots[0]['tables'])!=canonical(payload['tables']): raise ValueError('Snapshot import changed data')
        print(json.dumps({'postgres_restore':'passed','tables':{k:len(v) for k,v in payload['tables'].items()},'scope':'complete application public schema and data; Auth/platform excluded'}))
    finally:
        for name in names:
            subprocess.run(['dropdb','--if-exists','--maintenance-db='+url,name],capture_output=True)
