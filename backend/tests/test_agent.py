from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, BigInteger
from sqlalchemy.dialects.mysql import LONGTEXT, LONGBLOB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.resume import Resume
from app.api.routes import agent, auth, job_matches, custom_resumes
from app.ai.errors import AIServiceError
from app.schemas.job_match import JobMatchResult
from app.schemas.custom_resume import GeneratedCustomResumeResult
from test_job_match import VALID_RESULT as MATCH, JOB_DESCRIPTION, RESUME_TEXT
from test_custom_resume import VALID_RESULT as CUSTOM


@compiles(BigInteger, 'sqlite')
def bigint_sqlite(element, compiler, **kw):
    return 'INTEGER'


@compiles(LONGTEXT, 'sqlite')
def longtext_sqlite(element, compiler, **kw):
    return 'TEXT'


@compiles(LONGBLOB, 'sqlite')
def blob_sqlite(element, compiler, **kw):
    return 'BLOB'


@pytest.fixture
def client(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    def db():
        with Session(engine, expire_on_commit=False) as session:
            yield session
    app.dependency_overrides[get_db] = db
    monkeypatch.setattr(auth.auth_rate_limiter, 'check', lambda *a, **k: None)
    async def choose(data, allowed):
        return allowed[0], '正在完成本项准备', {'prompt_tokens': 1, 'completion_tokens': 1}
    async def match(*args, **kwargs):
        return SimpleNamespace(result=JobMatchResult.model_validate(MATCH), input_tokens=1, output_tokens=1)
    async def tailor(*args, **kwargs):
        return SimpleNamespace(result=GeneratedCustomResumeResult.model_validate(CUSTOM), input_tokens=1, output_tokens=1)
    async def prep(data):
        return {'summary': '准备方案', 'items': []}, 1, 1
    monkeypatch.setattr(agent, 'select_tool', choose)
    monkeypatch.setattr(job_matches, 'generate_job_match', match)
    monkeypatch.setattr(custom_resumes, 'generate_custom_resume', tailor)
    monkeypatch.setattr(agent, 'prepare', prep)
    with TestClient(app) as browser:
        user = browser.post('/api/v1/auth/guest').json()
        browser.headers['X-CSRF-Token'] = browser.cookies['ai_career_csrf']
        with Session(engine) as session:
            session.add(Resume(user_id=user['id'], original_name='test.docx', storage_key='test-only',
                mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', size_bytes=100,
                parsed_text=RESUME_TEXT, parse_status='ready', content_version=1, confirmed_at=datetime.now(UTC).replace(tzinfo=None)))
            session.commit()
        yield browser, engine
    app.dependency_overrides.clear()
    engine.dispose()


def create(browser, company='示例公司'):
    response = browser.post('/api/v1/agent', json={'job_title': '前端工程师', 'company_name': company, 'job_description': JOB_DESCRIPTION})
    assert response.status_code == 200, response.text
    return response.json()


def step(browser, run):
    response = browser.post(f"/api/v1/agent/{run['id']}/step", json={'revision': run['revision']})
    assert response.status_code == 200, response.text
    return response.json()


def test_guest_reuses_identity_and_cross_visitor_isolation(client):
    browser, _ = client
    me = browser.get('/api/v1/auth/me').json()
    assert browser.post('/api/v1/auth/guest').json()['id'] == me['id']
    browser.headers['X-CSRF-Token'] = browser.cookies['ai_career_csrf']
    run = create(browser)
    with TestClient(app) as stranger:
        assert stranger.get('/api/v1/agent/' + run['id']).status_code == 401
        stranger.post('/api/v1/auth/guest')
        assert stranger.get('/api/v1/agent/' + run['id']).status_code == 404
        assert stranger.get('/api/v1/agent').json() == []
        assert stranger.get('/api/v1/resumes/primary').json() is None
    assert 'resume_text' not in run


def test_company_role_name_and_optional_company(client):
    browser, _ = client
    assert create(browser)['title'] == '示例公司 · 前端工程师'
    assert create(browser, '')['title'] == '前端工程师'


def test_real_route_workflow_persists_and_exports(client):
    browser, _ = client
    run = create(browser)
    initial = run.copy()
    run = step(browser, run)
    assert run['match']['match_score'] == 60
    assert browser.post(f"/api/v1/agent/{run['id']}/step", json={'revision': initial['revision']}).status_code == 409
    run = step(browser, run)
    assert run['custom_resume_id']
    run = step(browser, run)
    assert run['preparation']
    run = step(browser, run)
    assert run['status'] == 'completed'
    assert browser.get('/api/v1/interviews/current').json() is None
    assert browser.get('/api/v1/agent/' + run['id']).json()['status'] == 'completed'
    cid = run['custom_resume_id']
    assert browser.post(f'/api/v1/custom-resumes/{cid}/export').status_code == 409
    custom = browser.get(f'/api/v1/custom-resumes/{cid}').json()
    assert custom['pending_count'] == 0
    assert all(not i['has_suggestion'] and i['decision'] == 'rejected'
        for s in custom['sections'] for i in s['items'])
    header = {k: v for k, v in custom['header'].items() if k != 'has_photo'}
    header['name'] = '测试用户'
    payload = {'header': header, 'sections': [{'title': s['title'], 'items': [{'decision': 'accepted', 'final_text': i['suggested_text']} for i in s['items']]} for s in custom['sections']]}
    assert browser.put(f'/api/v1/custom-resumes/{cid}', json=payload).status_code == 200
    pdf = browser.post(f'/api/v1/custom-resumes/{cid}/export')
    assert pdf.status_code == 200 and pdf.content.startswith(b'%PDF')
    word = browser.post(f'/api/v1/custom-resumes/{cid}/export/word')
    assert word.status_code == 200 and word.content.startswith(b'PK')
    from io import BytesIO
    from docx import Document
    document = Document(BytesIO(word.content))
    text = '\n'.join(p.text for p in document.paragraphs)
    for section in custom['sections']:
        for item in section['items']:
            assert item['source_text'] in text


def test_legacy_pending_cosmetic_advice_can_save_without_accepting(client):
    from app.models.ai import CustomResume
    browser, engine = client
    run = step(browser, step(browser, create(browser)))
    cid = run['custom_resume_id']
    with Session(engine) as session:
        record = session.get(CustomResume, cid)
        content = {**record.content, 'sections': [
            {**s, 'items': [{**i, 'decision': 'pending'} for i in s['items']]}
            for s in record.content['sections']]}
        record.content = content
        session.commit()
    custom = browser.get(f'/api/v1/custom-resumes/{cid}').json()
    assert custom['pending_count'] == 0
    header = {k: v for k, v in custom['header'].items() if k != 'has_photo'}
    header['name'] = '测试用户'
    payload = {'header': header, 'sections': [
        {'title': s['title'], 'items': [{'decision': 'pending', 'final_text': i['source_text']} for i in s['items']]}
        for s in custom['sections']]}
    saved = browser.put(f'/api/v1/custom-resumes/{cid}', json=payload).json()
    assert saved['status'] == 'ready'
    assert saved['pending_count'] == 0
    payload['sections'][0]['items'][0] = {'decision': 'custom', 'final_text': '用户主动编辑的最终内容'}
    saved = browser.put(f'/api/v1/custom-resumes/{cid}', json=payload).json()
    assert saved['sections'][0]['items'][0]['final_text'] == '用户主动编辑的最终内容'


def test_failure_retries_only_missing_step(client, monkeypatch):
    browser, _ = client
    run = step(browser, create(browser))
    previous_match = run['match']['id']
    async def fail(*a, **k):
        raise AIServiceError('AI_TIMEOUT', 'simulated')
    original = agent.select_tool
    monkeypatch.setattr(agent, 'select_tool', fail)
    run = step(browser, run)
    assert run['status'] == 'failed' and run['match']['id'] == previous_match
    monkeypatch.setattr(agent, 'select_tool', original)
    run = step(browser, run)
    assert run['custom_resume_id'] and run['match']['id'] == previous_match


def test_waiting_requires_reply_and_csrf(client, monkeypatch):
    browser, _ = client
    async def ask(*a):
        return 'ask_user', '请补充求职目标', {}
    monkeypatch.setattr(agent, 'select_tool', ask)
    run = step(browser, create(browser))
    assert run['status'] == 'waiting'
    assert step(browser, run)['revision'] == run['revision']
    browser.headers.pop('X-CSRF-Token')
    assert browser.post(f"/api/v1/agent/{run['id']}/reply", json={'message': '前端开发'}).status_code == 403
    browser.headers['X-CSRF-Token'] = browser.cookies['ai_career_csrf']
    result = browser.post(f"/api/v1/agent/{run['id']}/reply", json={'message': '前端开发'}).json()
    assert result['status'] == 'ready' and result['messages'][-1]['role'] == 'user'


def test_illegal_tool_is_rejected_and_changed_resume_blocks_execution(client, monkeypatch):
    browser, engine = client
    async def invalid(*a):
        return 'start_interview', '不应执行', {}
    monkeypatch.setattr(agent, 'select_tool', invalid)
    run = step(browser, create(browser))
    assert run['status'] == 'failed'
    with Session(engine) as session:
        row = session.query(Resume).first()
        row.content_version += 1
        session.commit()
    run = step(browser, run)
    assert 'Main CV updated' in run['error']


def test_optional_jd_and_whitespace_validation(client):
    browser, _ = client
    response = browser.post('/api/v1/agent', json={'job_title': '软件开发'})
    assert response.status_code == 200
    assert response.json()['generic_requirements'] is True
    assert response.json()['title'] == '软件开发'
    assert browser.post('/api/v1/agent', json={'job_title': '  '}).status_code == 422


def test_budget_is_shared_by_independent_database_sessions(client):
    from app.services.agent_budget import check_budget
    from fastapi import HTTPException
    _, engine = client
    with Session(engine) as first:
        check_budget(first, 'test-budget', limit=1, window_seconds=3600)
    with Session(engine) as second:
        with pytest.raises(HTTPException) as error:
            check_budget(second, 'test-budget', limit=1, window_seconds=3600)
        assert error.value.status_code == 429


def test_planner_executes_one_of_multiple_proposed_tools(monkeypatch):
    import asyncio
    import json
    from app.ai import agent as planner
    from app.core.config import Settings
    settings = Settings(deepseek_api_key='test-only-not-real', _env_file=None)
    monkeypatch.setattr(planner, 'DeepSeekClient', lambda: SimpleNamespace(settings=settings))
    calls = [{'function': {'name': name, 'arguments': json.dumps({'message': '准备执行'})}}
             for name in ['tailor_resume', 'prepare_interview']]
    class Transport:
        def __init__(self, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def post(self, *args, **kwargs):
            return SimpleNamespace(status_code=200, json=lambda: {
                'choices': [{'message': {'tool_calls': calls}}], 'usage': {}})
    monkeypatch.setattr(planner.httpx, 'AsyncClient', Transport)
    name, message, usage = asyncio.run(planner.select_tool({}, ['tailor_resume', 'prepare_interview']))
    assert name == 'tailor_resume'
    with pytest.raises(AIServiceError):
        asyncio.run(planner.select_tool({}, ['prepare_interview']))
