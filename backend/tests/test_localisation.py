import asyncio
import json
from io import BytesIO
from types import SimpleNamespace

import pymupdf
import pytest
from docx import Document
from fastapi.testclient import TestClient

from app.main import app
from app.localisation import request_language
from app.ai import client as model_client
from app.ai import agent as agent_ai
from app.ai.errors import AIServiceError
from app.core.config import Settings
from app.schemas.custom_resume import GeneratedCustomResumeResult, validate_generated_custom_resume
from app.schemas.interview import InterviewQuestionFeedback, validate_question_feedback
from app.schemas.job_match import JobMatchResult, validate_job_match_facts
from app.services.resume_header import extract_resume_header
from app.services.custom_resume_pdf import build_custom_resume_pdf
from app.services.custom_resume_docx import build_custom_resume_docx
from test_agent import client
from test_interview import FEEDBACK_RESULT
from test_job_match import VALID_RESULT, RESUME_TEXT, JOB_DESCRIPTION


def test_public_profile_defaults_to_english_and_can_switch_back():
    with TestClient(app) as browser:
        for language, name in [('en-GB', 'Tianyu Qi'), ('zh-CN', '齐天宇'), ('en-GB', 'Tianyu Qi')]:
            response = browser.get('/api/v1/persona/profile', headers={'Accept-Language': language})
            assert response.status_code == 200
            assert response.json()['name'] == name
            assert response.headers['Content-Language'] == language
            assert 'Accept-Language' in response.headers['Vary']
            assert 'contact' not in response.json()
        assert browser.get('/api/v1/persona/profile').json()['name'] == 'Tianyu Qi'


def test_api_validation_errors_follow_selected_language(client):
    browser, _ = client
    request = {'parsed_text': 'short' + ' ' * 30}
    english = browser.put('/api/v1/resumes/primary/text', json=request, headers={'Accept-Language':'en-GB'})
    chinese = browser.put('/api/v1/resumes/primary/text', json=request, headers={'Accept-Language':'zh-CN'})
    assert english.status_code == chinese.status_code == 422
    assert 'CV text' in english.json()['detail'][0]['msg']
    assert '简历文字' in chinese.json()['detail'][0]['msg']


def test_english_missing_evidence_is_valid_but_ability_claim_is_rejected():
    payload = json.loads(json.dumps(VALID_RESULT))
    for item in payload['missing_items']: item['explanation'] = 'This skill is not evidenced in the CV.'
    validate_job_match_facts(JobMatchResult.model_validate(payload), RESUME_TEXT, JOB_DESCRIPTION)
    payload['missing_items'][0]['explanation'] = 'You cannot use this technology.'
    with pytest.raises(ValueError):
        validate_job_match_facts(JobMatchResult.model_validate(payload), RESUME_TEXT, JOB_DESCRIPTION)


def test_english_feedback_prose_is_not_mistaken_for_invented_technology():
    feedback = InterviewQuestionFeedback.model_validate({**FEEDBACK_RESULT,
        'strengths':['Your example explains the file upload clearly.'],
        'issues':['The answer needs more detail about your individual contribution.'],
        'suggestions':['Explain the task you owned.', 'Describe the result without inventing metrics.'],
        'answer_outline':['Introduce the context.', 'Explain your action.', 'Describe the real outcome.']})
    validate_question_feedback(feedback, 'I implemented file upload validation in Vue.')
    feedback.strengths = ['Your example demonstrates experience with React.']
    with pytest.raises(ValueError): validate_question_feedback(feedback, 'I implemented file upload validation in Vue.')


def test_english_cv_rewording_keeps_technical_and_numeric_checks():
    source = 'Developed Vue pages. Implemented FastAPI endpoints.'
    result = GeneratedCustomResumeResult.model_validate({'sections':[{'title':'Projects','items':[
        {'source_text':'Developed Vue pages.', 'suggested_text':'Developed pages using Vue.', 'reason':'Clarifies the implementation.'},
        {'source_text':'Implemented FastAPI endpoints.', 'suggested_text':'Implemented endpoints using FastAPI.', 'reason':'Keeps the original facts.'}]}], 'missing_information_warnings':[]})
    validate_generated_custom_resume(result, source)
    result.sections[0].items[0].suggested_text = 'Developed React pages.'
    with pytest.raises(ValueError): validate_generated_custom_resume(result, source)


def test_english_cv_header_and_international_phone():
    header = extract_resume_header('Alex Morgan\nPhone: +44 7700 900123\nalex@example.com\nLocation: London\nEducation\nUniversity Example')
    assert header['name'] == 'Alex Morgan'
    assert header['phone'] == '+44 7700 900123'
    assert header['location'] == 'London'


@pytest.mark.parametrize('language, label, footer', [('en','Phone','Page 1'), ('zh','联系电话','第 1 页')])
def test_exports_localise_labels_without_changing_user_content(language, label, footer):
    resume = SimpleNamespace(content={'header':{'name':'Alex Morgan','phone':'+44 7700 900123','email':'alex@example.com'},
        'sections':[{'title':'Projects','items':[{'item_type':'bullet','final_text':'Developed a Vue portfolio.'}]}]})
    token = request_language.set(language)
    try:
        pdf = build_custom_resume_pdf(resume)
        word = Document(BytesIO(build_custom_resume_docx(resume)))
    finally: request_language.reset(token)
    with pymupdf.open(stream=pdf, filetype='pdf') as document:
        text = '\n'.join(page.get_text() for page in document)
        assert label in text
        assert footer in text
        assert 'Developed a Vue portfolio.' in text
    xml = word.element.xml
    assert label in xml
    assert 'Developed a Vue portfolio.' in xml


def test_model_language_is_request_scoped_even_for_concurrent_visitors(monkeypatch):
    class FakeHTTP:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, headers, json):
            await asyncio.sleep(0)
            prompt = json['messages'][0]['content']
            return SimpleNamespace(status_code=200, json=lambda:{'choices':[{'message':{'content':__import__('json').dumps({'prompt':prompt})},'finish_reason':'stop'}]})
    monkeypatch.setattr(model_client.httpx, 'AsyncClient', FakeHTTP)
    settings = Settings(auth_secret='test-only-auth-secret-with-more-than-32-characters', deepseek_api_key='test-placeholder')
    async def call(language):
        token = request_language.set(language)
        try: return (await model_client.DeepSeekClient(settings).complete_json('Use verified facts only.', '{}')).data['prompt']
        finally: request_language.reset(token)
    async def run(): return await asyncio.gather(call('en'), call('zh'), call('en'))
    english, chinese, english_again = asyncio.run(run())
    assert 'British English' in english and english == english_again
    assert 'Simplified Chinese' in chinese and 'British English' not in chinese
    assert request_language.get() == 'en'


def test_planner_retries_invalid_tool_selection_but_not_bad_credentials(monkeypatch):
    calls = []
    async def once(data, allowed):
        calls.append(1)
        if len(calls) == 1: raise AIServiceError('AI_RESPONSE_INVALID', 'Invalid response')
        return 'analyze_job', 'Analyse the role.', {}
    monkeypatch.setattr(agent_ai, '_select_tool_once', once)
    assert asyncio.run(agent_ai.select_tool({}, ['analyze_job']))[0] == 'analyze_job'
    assert len(calls) == 2
    async def unauthorised(data, allowed):
        calls.append(1)
        raise AIServiceError('AI_AUTH_FAILED', 'Invalid credentials')
    monkeypatch.setattr(agent_ai, '_select_tool_once', unauthorised)
    with pytest.raises(AIServiceError): asyncio.run(agent_ai.select_tool({}, ['analyze_job']))
    assert len(calls) == 3


def test_preparation_retries_invalid_schema(monkeypatch):
    calls = []
    async def complete(self, system, user):
        calls.append(1)
        items = [{'title':'Role preparation','focus':'Review your real project work.','question':'Which part did you contribute?','outline':['Explain your contribution.']}] * 3
        return SimpleNamespace(data={'summary':'A focused preparation plan.','items':[] if len(calls)==1 else items},input_tokens=1,output_tokens=1)
    monkeypatch.setattr(agent_ai.DeepSeekClient, 'complete_json', complete)
    result = asyncio.run(agent_ai.prepare({}))
    assert len(result[0]['items']) == 3 and len(calls) == 2
