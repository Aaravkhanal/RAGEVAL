"""Fetch an admin snapshot, verify encryption round trip, upload ciphertext only."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import subprocess
import tempfile
import httpx


def fetch_snapshot():
    with httpx.Client(timeout=120) as client:
        response=client.get(os.environ.get('RAGEVAL_BASE_URL','https://rageval-free.onrender.com')+'/workspace/backup',headers={
            'X-RAGEVAL-API-TOKEN':os.environ['RAGEVAL_PUBLIC_TOKEN'],
            'X-RAGEVAL-ADMIN-TOKEN':os.environ['RAGEVAL_ADMIN_TOKEN']})
        response.raise_for_status()
        payload=response.json()
    if payload.get('schema')!='rageval.logical_backup.v1' or set(payload['tables'])!={'rageval_records','rageval_jobs'}:
        raise ValueError('Unexpected snapshot format')
    return payload


def encrypt_snapshot(payload, destination):
    if len(os.environ.get('RAGEVAL_BACKUP_KEY',''))<32:
        raise ValueError('Backup encryption key must contain at least 32 characters')
    destination=Path(destination)
    if destination.exists(): raise ValueError('Refusing to overwrite an existing backup')
    with tempfile.TemporaryDirectory() as folder:
        plain=Path(folder)/'snapshot.json'
        plain.write_text(json.dumps(payload,sort_keys=True))
        plain.chmod(0o600)
        subprocess.run(['openssl','enc','-aes-256-cbc','-salt','-pbkdf2','-iter','200000','-pass','env:RAGEVAL_BACKUP_KEY','-in',str(plain),'-out',str(destination)],check=True,capture_output=True)
        mac_key=hashlib.sha256(b'rageval-backup-hmac-v1'+os.environ['RAGEVAL_BACKUP_KEY'].encode()).digest()
        destination.with_suffix(destination.suffix+'.hmac').write_text(hmac.new(mac_key,destination.read_bytes(),hashlib.sha256).hexdigest()+'\n')
        recovered=Path(folder)/'recovered.json'
        decrypt_snapshot(destination,recovered)
        if json.loads(recovered.read_text())!=payload: raise ValueError('Encryption round trip failed')
    digest=hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(destination.suffix+'.sha256').write_text(digest+'\n')
    return digest


def decrypt_snapshot(source, destination):
    source,destination=Path(source),Path(destination)
    key=os.environ['RAGEVAL_BACKUP_KEY']
    mac_key=hashlib.sha256(b'rageval-backup-hmac-v1'+key.encode()).digest()
    expected=source.with_suffix(source.suffix+'.hmac').read_text().strip()
    if not hmac.compare_digest(expected,hmac.new(mac_key,source.read_bytes(),hashlib.sha256).hexdigest()):
        raise ValueError('Backup authentication failed; wrong key or corrupted backup')
    with destination.open('x') as out:
        destination.chmod(0o600)
    subprocess.run(['openssl','enc','-d','-aes-256-cbc','-pbkdf2','-iter','200000','-pass','env:RAGEVAL_BACKUP_KEY','-in',str(source),'-out',str(destination)],check=True,capture_output=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='rageval-backup.enc')
    parser.add_argument('--verify-postgres',action='store_true')
    args=parser.parse_args()
    snapshot=fetch_snapshot()
    if args.verify_postgres:
        from scripts.verify_postgres_restore import verify
        verify(snapshot)
    digest=encrypt_snapshot(snapshot,args.output)
    print(json.dumps({'encrypted_backup':args.output,'sha256':digest,'table_counts':{k:len(v) for k,v in snapshot['tables'].items()}}))
