from scripts import backup_remote
import pytest


def test_logical_backup_restore_and_project_guard(monkeypatch):
    written=[]
    rows={table:[{'id':table,'value':'preserved'}] for table in backup_remote.TABLES}
    def request(table,method='GET',body=None,query=''):
        if method=='GET': return rows[table]
        written.append((table,body))
    monkeypatch.setattr(backup_remote,'request',request)
    monkeypatch.setenv('RAGEVAL_SUPABASE_URL','https://isolated-test.supabase.co')
    payload=backup_remote.backup()
    with pytest.raises(ValueError): backup_remote.restore(payload,'wrong-project')
    assert not written
    backup_remote.restore(payload,'isolated-test')
    assert dict(written)==rows
