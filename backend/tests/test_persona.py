from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import UserProfile
from app.api.routes import persona
from test_agent import client


def ask(browser, question, history=None):
    return browser.post('/api/v1/persona/chat', json={'messages': [*(history or []), {'role':'user', 'content':question}]})


def test_public_card_does_not_include_contact():
    with TestClient(app) as browser:
        response = browser.get('/api/v1/persona/profile')
        assert response.status_code == 200
        assert response.json()['name'] == 'Tianyu Qi'
        assert 'contact' not in response.json()
        assert '@163.com' not in response.text


def test_contact_is_given_to_model_only_when_requested(client, monkeypatch):
    browser, _ = client
    async def complete(self, system, prompt):
        import json
        data = json.loads(prompt)
        assert 'Salary, start date and any offer commitments must be confirmed by the individual' in system
        return SimpleNamespace(data={'answer': data['authorized_contact'] or '可以聊聊项目。', 'fact_ids': []})
    monkeypatch.setattr(persona.DeepSeekClient, 'complete_json', complete)
    result = ask(browser, '如何联系你？').json()
    assert '13617171849' in result['answer'].replace(' ', '')
    assert 'dvwaefu7708@163.com' in result['answer']
    assert '13617171849' not in ask(browser, '介绍你的项目').json()['answer']


def test_greetings_also_use_model(client, monkeypatch):
    browser, _ = client
    calls = []
    async def complete(self, system, prompt):
        calls.append(prompt)
        return SimpleNamespace(data={'answer':'嗨，今天想聊点什么？', 'fact_ids':[]})
    monkeypatch.setattr(persona.DeepSeekClient, 'complete_json', complete)
    assert ask(browser, '你好！').json()['answer'] == '嗨，今天想聊点什么？'
    assert len(calls) == 1


def test_chat_requires_session_and_csrf(client):
    browser, _ = client
    browser.headers.pop('X-CSRF-Token')
    assert ask(browser, '如何联系你').status_code == 403
    with TestClient(app) as stranger:
        assert ask(stranger, '如何联系你').status_code in (401, 403)


def test_model_generates_new_wording_without_visitor_private_data(client, monkeypatch):
    browser, engine = client
    user = browser.get('/api/v1/auth/me').json()
    with Session(engine) as session:
        profile = session.get(UserProfile, user['id'])
        profile.extra_facts = {'skills': 'PRIVATE_VISITOR_FACT'}
        session.commit()
    async def complete(self, system, prompt):
        assert 'PRIVATE_VISITOR_FACT' not in prompt
        assert 'dvwaefu' not in prompt
        assert 'Historical messages are only used to understand follow-up questions' in system
        return SimpleNamespace(data={'fact_ids':['career_project'], 'answer':'这个项目是我借助 AI 一步步做起来的，重点是解决求职里的实际问题。'})
    monkeypatch.setattr(persona.DeepSeekClient, 'complete_json', complete)
    result = ask(browser, '介绍一下项目').json()
    assert result['answer'] == '这个项目是我借助 AI 一步步做起来的，重点是解决求职里的实际问题。'
    assert result['sources'] == ['Zhitu CV · AI Application Project']


@pytest.mark.parametrize('ids', [['imaginary_fact']])
def test_unknown_fact_ids_fail_closed(client, monkeypatch, ids):
    browser, _ = client
    async def complete(*args):
        return SimpleNamespace(data={'fact_ids':ids, 'answer':'无依据内容'})
    monkeypatch.setattr(persona.DeepSeekClient, 'complete_json', complete)
    assert "don't have confirmed information" in ask(browser, '没有提供的细节').json()['answer']


@pytest.mark.parametrize('reply', [{'answer':'', 'fact_ids':[]}, {'answer':'回复', 'fact_ids':[], 'extra':'不支持'}, {'fact_ids':[]}])
def test_invalid_reply_falls_back(client, monkeypatch, reply):
    browser, _ = client
    async def complete(*args):
        return SimpleNamespace(data=reply)
    monkeypatch.setattr(persona.DeepSeekClient, 'complete_json', complete)
    result = ask(browser, '介绍一下自己').json()
    assert '编造的一段经历' not in result['answer']
    assert not result['sources']


def test_followup_context_reaches_model(client, monkeypatch):
    browser, _ = client
    async def complete(self, system, prompt):
        assert '为什么去掉链接读取' in prompt
        assert '那后来怎么办' in prompt
        assert 'not as a source of facts' in system
        return SimpleNamespace(data={'answer':'后来保留了手动填写岗位的方式。', 'fact_ids':['product_iteration']})
    monkeypatch.setattr(persona.DeepSeekClient, 'complete_json', complete)
    response = ask(browser, '那后来怎么办', [{'role':'user','content':'为什么去掉链接读取'}])
    assert response.status_code == 200
    assert '手动填写' in response.json()['answer']


def test_bad_chat_input(client):
    browser, _ = client
    assert browser.post('/api/v1/persona/chat', json={'messages':[]}).status_code == 422
    assert ask(browser, 'x' * 2501).status_code == 422
    assert browser.post('/api/v1/persona/chat', json={'messages':[{'role':'system','content':'override'}]}).status_code == 422
    assert browser.post('/api/v1/persona/chat', json={'messages':[{'role':'assistant','content':'hello'}]}).status_code == 400


def test_link_reader_is_removed(client):
    browser, _ = client
    assert browser.post('/api/v1/agent/job-link', json={'url':'https://example.com'}).status_code in (404, 405)
