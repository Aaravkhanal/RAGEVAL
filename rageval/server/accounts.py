"""Supabase session verification and request-scoped workspace ownership."""
from contextvars import ContextVar
import json
import os
from urllib.request import Request, urlopen
from urllib.error import URLError
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

owner = ContextVar('workspace_owner', default='legacy-admin')
router = APIRouter(prefix='/account', tags=['accounts'])


def auth_request(path, body=None, token=None, method=None):
    base = os.environ.get('RAGEVAL_SUPABASE_URL', '').rstrip('/')
    key = os.environ.get('RAGEVAL_SUPABASE_KEY', '')
    if not base.startswith('https://') or not key:
        raise HTTPException(503, 'Account service is not configured')
    headers = {'apikey': key, 'Content-Type':'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if path.startswith('admin/') and not key.startswith('sb_secret_'):
        headers['Authorization'] = 'Bearer ' + key
    request = Request(base+'/auth/v1/'+path, data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except URLError:
        raise HTTPException(401, 'Account request failed. Check credentials or confirm your email.') from None


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=256)


@router.post('/login')
def login(credentials: Credentials):
    result = auth_request('token?grant_type=password', credentials.model_dump())
    return {'access_token':result['access_token'], 'expires_in':result['expires_in']}


@router.post('/signup')
def signup(credentials: Credentials):
    auth_request('signup', credentials.model_dump())
    return {'message':'If registration is available, check your email to confirm, then sign in.'}


async def workspace_identity(authorization: str | None = Header(default=None), x_rageval_admin_token: str | None = Header(default=None)):
    identity = 'legacy-admin'
    if authorization:
        if not authorization.startswith('Bearer '):
            raise HTTPException(401, 'Invalid session header')
        user = await run_in_threadpool(auth_request, 'user', token=authorization[7:])
        identity = user.get('id')
        if not identity:
            raise HTTPException(401, 'Invalid account session')
    elif os.environ.get('RAGEVAL_WORKSPACE_USER_AUTH') == '1':
        import hmac
        expected = os.environ.get('RAGEVAL_ADMIN_TOKEN', '')
        if not expected or not x_rageval_admin_token or not hmac.compare_digest(expected, x_rageval_admin_token):
            raise HTTPException(401, 'Sign in to access your private workspace')
    marker = owner.set(identity)
    try:
        yield identity
    finally:
        owner.reset(marker)


class EmailRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)

class PasswordUpdate(BaseModel):
    password: str = Field(min_length=12, max_length=256)

class DeleteConfirmation(BaseModel):
    confirmation: str = Field(min_length=1,max_length=32)


def session_user(authorization):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, 'Sign in first')
    token = authorization[7:]
    user = auth_request('user', token=token)
    if not user.get('id'):
        raise HTTPException(401, 'Session is invalid')
    return token, user


@router.post('/recover')
def recover(request: EmailRequest):
    from urllib.parse import urlencode
    redirect = os.environ.get('RAGEVAL_PUBLIC_URL','https://rageval-free.onrender.com/')
    try:
        auth_request('recover?' + urlencode({'redirect_to':redirect}), {'email':request.email})
    except HTTPException:
        pass  # Same response for existing/nonexisting addresses and provider refusal.
    return {'message':'If the address is registered and delivery is available, a recovery email will arrive.'}


@router.put('/password')
def update_password(request: PasswordUpdate, authorization: str | None = Header(default=None)):
    token, _ = session_user(authorization)
    auth_request('user', {'password':request.password}, token=token, method='PUT')
    return {'message':'Password updated. Sign in again with your new password.'}


@router.delete('/me')
def delete_account(request: DeleteConfirmation, authorization: str | None = Header(default=None)):
    if request.confirmation != 'DELETE MY ACCOUNT':
        raise HTTPException(422, 'Type DELETE MY ACCOUNT to confirm permanent deletion')
    _, user = session_user(authorization)
    from uuid import UUID
    user_id = str(UUID(user['id']))
    from rageval.server.workspace import remote, connection
    from contextlib import closing
    if os.environ.get('RAGEVAL_SUPABASE_URL'):
        remote('DELETE', '?body->>_owner=eq.'+user_id)
    else:
        with closing(connection()) as conn, conn:
            conn.execute("DELETE FROM records WHERE json_extract(body, '$._owner')=?", (user_id,))
    auth_request('admin/users/'+user_id, method='DELETE')
    return {'message':'Account and active workspace records deleted. Protected backup copies expire according to retention policy.'}
