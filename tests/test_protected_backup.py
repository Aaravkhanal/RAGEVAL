import json
from pathlib import Path
import subprocess
import pytest
from scripts.protected_backup import encrypt_snapshot, decrypt_snapshot


def test_encrypted_backup_round_trip_and_wrong_key(tmp_path,monkeypatch):
    monkeypatch.setenv('RAGEVAL_BACKUP_KEY','test-only-encryption-key-at-least-32-characters')
    payload={'schema':'rageval.logical_backup.v1','tables':{'rageval_records':[{'private':'do not upload plaintext'}],'rageval_jobs':[]}}
    dest=tmp_path/'backup.enc'
    digest=encrypt_snapshot(payload,dest)
    assert len(digest)==64
    assert b'do not upload plaintext' not in dest.read_bytes()
    assert dest.with_suffix('.enc.sha256').read_text().strip()==digest
    decrypt_snapshot(dest,tmp_path/'restored.json')
    assert json.loads((tmp_path/'restored.json').read_text())==payload
    monkeypatch.setenv('RAGEVAL_BACKUP_KEY','wrong-test-only-encryption-key-long-enough')
    with pytest.raises(ValueError): decrypt_snapshot(dest,tmp_path/'wrong-key.json')
    assert not (tmp_path/'wrong-key.json').exists()
    result=subprocess.run(['openssl','enc','-d','-aes-256-cbc','-pbkdf2','-iter','200000','-pass','env:RAGEVAL_BACKUP_KEY','-in',str(dest)],capture_output=True)
    assert result.returncode!=0
    with pytest.raises(ValueError): encrypt_snapshot(payload,dest)
