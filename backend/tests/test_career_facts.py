from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.custom_resume import GeneratedCustomResumeResult, build_editable_sections, CustomResumeSection
from app.api.routes import custom_resumes, job_matches
from app.schemas.job_match import JobMatchResult
from test_agent import client, create, step
from test_job_match import VALID_RESULT as MATCH


def test_facts_saved_private_and_revision_protected(client):
    browser, _ = client
    facts = browser.get('/api/v1/profile/facts').json()
    assert facts['revision'] == 0
    facts['skills'] = 'Python：完成课程数据清洗项目'
    saved = browser.put('/api/v1/profile/facts', json=facts)
    assert saved.status_code == 200
    assert browser.get('/api/v1/profile/facts').json()['skills'] == facts['skills']
    assert browser.put('/api/v1/profile/facts', json=facts).status_code == 409
    with TestClient(app) as stranger:
        assert stranger.get('/api/v1/profile/facts').status_code == 401
        stranger.post('/api/v1/auth/guest')
        assert stranger.get('/api/v1/profile/facts').json()['skills'] == ''
    browser.headers.pop('X-CSRF-Token')
    assert browser.put('/api/v1/profile/facts', json={**facts, 'revision': 1}).status_code == 403


def test_run_detects_new_facts_without_rewriting_old_run(client):
    browser, _ = client
    run = create(browser)
    browser.put('/api/v1/profile/facts', json={'skills': 'Python数据清洗课程项目', 'revision': 0})
    result = step(browser, run)
    assert result['status'] == 'failed'
    assert 'Personal details updated' in result['error']
    assert create(browser)['facts_revision'] == 1


def test_supplement_reaches_match_and_resume_requires_confirmation(client, monkeypatch):
    browser, _ = client
    extra = '使用 Python 完成课程数据清洗项目，负责空值处理与数据校验。'
    browser.put('/api/v1/profile/facts', json={'experiences': extra, 'revision': 0})
    async def match(text, *args, **kwargs):
        assert extra in text
        return SimpleNamespace(result=JobMatchResult.model_validate(MATCH), input_tokens=1, output_tokens=1)
    from test_custom_resume import VALID_RESULT as CUSTOM
    async def tailor(text, *args, **kwargs):
        assert extra in text
        data = {'sections': [{'title': '项目经历', 'items': [
            CUSTOM['sections'][0]['items'][0],
            {'source_text': extra, 'suggested_text': extra, 'reason': '补充岗位相关实践'}]}],
            'missing_information_warnings': []}
        return SimpleNamespace(result=GeneratedCustomResumeResult.model_validate(data), input_tokens=1, output_tokens=1)
    monkeypatch.setattr(job_matches, 'generate_job_match', match)
    monkeypatch.setattr(custom_resumes, 'generate_custom_resume', tailor)
    run = step(browser, step(browser, create(browser)))
    cid = run['custom_resume_id']
    data = browser.get(f'/api/v1/custom-resumes/{cid}').json()
    addition = data['sections'][0]['items'][1]
    assert addition['source_kind'] == 'supplement'
    assert addition['has_suggestion'] and addition['decision'] == 'pending'
    assert addition['final_text'] == ''
    header = {k: v for k, v in data['header'].items() if k != 'has_photo'}
    header['name'] = '测试用户'
    payload = {'header': header, 'sections': [{'title': s['title'], 'items': [
        {'decision': 'rejected', 'final_text': i['source_text']} for i in s['items']
    ]} for s in data['sections']]}
    saved = browser.put(f'/api/v1/custom-resumes/{cid}', json=payload).json()
    assert saved['sections'][0]['items'][1]['final_text'] == ''
    payload['sections'][0]['items'][1]['decision'] = 'accepted'
    saved = browser.put(f'/api/v1/custom-resumes/{cid}', json=payload).json()
    assert saved['sections'][0]['items'][1]['final_text'] == extra
    assert saved['status'] == 'ready'
