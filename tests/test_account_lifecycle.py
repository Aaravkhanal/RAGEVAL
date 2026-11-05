from fastapi.testclient import TestClient
from rageval.server.app import app
from rageval.server.runtime import reset_runtime_for_tests
from rageval.server import accounts
import pytest

@pytest.fixture
def client(monkeypatch,tmp_path):
    reset_runtime_for_tests()
    monkeypatch.setenv('RAGEVAL_WORKSPACE_DB',str(tmp_path/'workspace.db'))
    monkeypatch.delenv('RAGEVAL_SUPABASE_URL',raising=False)
    monkeypatch.setenv('RAGEVAL_REQUIRE_AUTH','0')
    yield TestClient(app)
    reset_runtime_for_tests()


def test_recovery_does_not_reveal_account_existence(client,monkeypatch):
    def denied(*a,**k): raise accounts.HTTPException(401,'private error')
    monkeypatch.setattr(accounts,'auth_request',denied)
    response=client.post('/account/recover',json={'email':'test@example.com'})
    assert response.status_code==200
    assert 'private error' not in response.text


def test_password_requires_session_and_uses_authenticated_put(client,monkeypatch):
    calls=[]
    def auth(path,body=None,token=None,method=None):
        calls.append((path,body,token,method))
        return {'id':'11111111-1111-4111-8111-111111111111'}
    monkeypatch.setattr(accounts,'auth_request',auth)
    assert client.put('/account/password',json={'password':'strong-test-password'}).status_code==401
    assert client.put('/account/password',headers={'Authorization':'Bearer session'},json={'password':'strong-test-password'}).status_code==200
    assert calls[-1]==('user',{'password':'strong-test-password'},'session','PUT')


def test_delete_requires_exact_confirmation_and_removes_only_owner(client,monkeypatch):
    from rageval.server.workspace import save,records
    user='11111111-1111-4111-8111-111111111111'
    marker=accounts.owner.set(user)
    save('dataset',{'name':'owned'})
    accounts.owner.reset(marker)
    save('dataset',{'name':'admin-owned'})
    calls=[]
    def auth(path,body=None,token=None,method=None):
        calls.append((path,method))
        return {'id':user}
    monkeypatch.setattr(accounts,'auth_request',auth)
    header={'Authorization':'Bearer session'}
    assert client.request('DELETE','/account/me',headers=header,json={'confirmation':'no'}).status_code==422
    assert not calls
    assert client.request('DELETE','/account/me',headers=header,json={'confirmation':'DELETE MY ACCOUNT'}).status_code==200
    assert calls[-1]==('admin/users/'+user,'DELETE')
    assert records('dataset')[0]['name']=='admin-owned'
    marker=accounts.owner.set(user)
    assert records('dataset')==[]
    accounts.owner.reset(marker)

@pytest.mark.parametrize('code_field', ['error_code', 'code'])
def test_mail_restriction_and_quota_are_actionable_without_echoing_address(client,monkeypatch,code_field):
    from urllib.error import HTTPError
    import io,json
    monkeypatch.setenv('RAGEVAL_SUPABASE_URL','https://example.supabase.co')
    monkeypatch.setenv('RAGEVAL_SUPABASE_KEY','test-only-key')
    for code,status in [('email_address_not_authorized',503),('over_email_send_rate_limit',429)]:
        def refused(*args,**kwargs):
            raise HTTPError('https://example.supabase.co',400,'refused',{},io.BytesIO(json.dumps({code_field:code,'msg':'private-recipient@example.com'}).encode()))
        monkeypatch.setattr('rageval.server.accounts.urlopen',refused)
        response=client.post('/account/resend',json={'email':'test@example.com'})
        assert response.status_code==status
        assert 'private-recipient' not in response.text
