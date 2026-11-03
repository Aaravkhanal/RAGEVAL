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


def auth_request(path, body=None, token=None):
    base = os.environ.get('RAGEVAL_SUPABASE_URL', '').rstrip('/')
    key = os.environ.get('RAGEVAL_SUPABASE_KEY', '')
    if not base.startswith('https://') or not key:
        raise HTTPException(503, 'Account service is not configured')
    headers = {'apikey': key, 'Content-Type':'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = Request(base+'/auth/v1/'+path, data=json.dumps(body).encode() if body is not None else None, headers=headers)
    try:
        with urlopen(request, timeout=15) as response:
            return json.load(response)
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
