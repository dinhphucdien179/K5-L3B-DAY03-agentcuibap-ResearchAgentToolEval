"""Offline integration checks for the unified application, evidence and delivery."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_ui(monkeypatch, tmp_path):
    import ui.runtime as runtime
    empty_env = tmp_path / 'empty.env'
    empty_env.write_text('')
    monkeypatch.setenv('DAY03_ENV_FILE', str(empty_env))
    monkeypatch.setenv('NEXUS_TRANSCRIPTS_DIR', str(tmp_path / 'transcripts'))
    for key in ('OPENROUTER_API_KEY', 'OPENAI_API_KEY', 'GROQ_API_KEY', 'GEMINI_API_KEY', 'ANTHROPIC_API_KEY', 'TELEGRAM_BOT_TOKEN', 'RESEARCH_ALLOW_SEND'):
        monkeypatch.delenv(key, raising=False)
    return runtime, tmp_path / 'transcripts'


def open_app():
    app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=20)
    assert not app.exception
    return app


def submit(app, text):
    next(x for x in app.text_area if x.key == 'chat_draft').input(text)
    next(x for x in app.button if x.label.startswith('Gửi yêu cầu')).click().run(timeout=20)
    assert not app.exception


def last_turn(app):
    return app.session_state['nexus_session']['transcript']['turns'][-1]


def test_ui_opens_without_credentials_or_network(isolated_ui, monkeypatch):
    import providers
    monkeypatch.setattr(providers, 'make_provider', lambda *a: pytest.fail('Unexpected provider request'))
    page = open_app()
    assert any('OPENAI_API_KEY' in x.value for x in page.warning)
    assert any('Pipeline' in x.label for x in page.tabs)
    assert any('Research board' in x.label for x in page.tabs)
    assert any('So sánh có bằng chứng' in x.label for x in page.button)
    assert any('Kiểm tra trích dẫn' in x.label for x in page.button)
    assert not isolated_ui[1].exists()


def fake_chat(monkeypatch, runtime, result):
    import providers
    monkeypatch.setenv('OPENAI_API_KEY', 'offline-openai-key')
    monkeypatch.setattr(providers, 'make_provider', lambda name: object())
    calls = []
    def execute(**kwargs):
        calls.append(kwargs)
        return result
    monkeypatch.setattr(runtime, 'run_turn', execute)
    return calls


def test_ui_chat_records_real_loop_result_and_shows_tool_failures(isolated_ui, monkeypatch):
    calls = fake_chat(monkeypatch, isolated_ui[0], {'status':'answered', 'assistant_text':'Chưa đủ dữ liệu.', 'rounds':[],
        'tool_events':[{'tool':'lookup','args':{},'result':{'error':'rate_limited','message':'HTTP 429'}}]})
    page = open_app()
    submit(page, 'Nghiên cứu RAG')
    assert len(calls) == 1
    assert calls[0]['model'] == 'gpt-4o-mini'
    assert calls[0]['messages'][-1]['content'] == 'Nghiên cứu RAG'
    assert any('rate_limited' in x.value for x in page.warning)
    saved = json.loads(next(isolated_ui[1].glob('*.json')).read_text())
    assert saved['turns'][-1]['tool_events'][0]['tool'] == 'lookup'


def pending_chat(monkeypatch, runtime):
    monkeypatch.setenv('RESEARCH_ALLOW_SEND', '1')
    fake_chat(monkeypatch, runtime, {'status':'blocked', 'assistant_text':'Chờ duyệt bản nháp.', 'rounds':[],
        'tool_events':[{'tool':'send','args':{'text':'Bản nghiên cứu đã duyệt — có nguồn.'},'result':{'status':'blocked'}}]})
    return 'Bản nghiên cứu đã duyệt — có nguồn.'


def test_ui_requires_button_for_exact_telegram_payload(isolated_ui, monkeypatch):
    import chat
    draft = pending_chat(monkeypatch, isolated_ui[0])
    sends = []
    def execute(call, **kwargs):
        sends.append((call, kwargs))
        return {'tool':'send','args':call.args,'result':{'status':'sent'}}
    monkeypatch.setattr(chat, 'execute_tool_call', execute)
    page = open_app()
    submit(page, 'Gửi Telegram')
    assert sends == []
    assert any(x.value == draft for x in page.code)
    next(x for x in page.button if x.label == 'Xác nhận gửi Telegram').click().run(timeout=20)
    assert not page.exception
    assert len(sends) == 1
    assert sends[0][0].args == {'text':draft,'confirmed':True}
    assert sends[0][1] == {'confirmed_send_text':draft}
    assert last_turn(page)['tool_events'][0]['result']['status'] == 'sent'
    assert not any(x.label == 'Xác nhận gửi Telegram' for x in page.button)


def test_ui_redacts_credentials_and_filters_unsafe_source_links(isolated_ui, monkeypatch):
    from app import extract_sources, redact
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'very-secret-token')
    assert redact({'error':'request very-secret-token', 'api_key':'hidden'}) == {'error':'request [REDACTED]', 'api_key':'[REDACTED]'}
    sources = extract_sources([{'result':{'sources':[
        {'url':'javascript:alert(1)'},
        {'url':'https://example.com/paper','title':'Paper','excerpts':[{'text':'Evidence'}]},
        {'url':'https://example.com/paper','title':'Duplicate'},
        {'url':'https://user:password@example.org/private'}]}}])
    assert len(sources) == 1
    assert sources[0]['title'] == 'Paper'
    assert sources[0]['excerpt'] == 'Evidence'


@pytest.mark.parametrize('action', ['cancel','new_message','new_session'])
def test_pending_send_expires_when_user_moves_on(isolated_ui, monkeypatch, action):
    import chat
    pending_chat(monkeypatch, isolated_ui[0])
    sends = []
    monkeypatch.setattr(chat, 'execute_tool_call', lambda *a, **kw: sends.append(a))
    page = open_app()
    submit(page, 'Chuẩn bị gửi')
    if action == 'cancel':
        next(x for x in page.button if x.label == 'Hủy gửi').click().run(timeout=20)
        assert last_turn(page)['send_confirmation']['status'] == 'cancelled'
    elif action == 'new_session':
        next(x for x in page.button if 'Phiên mới' in x.label).click().run(timeout=20)
        assert page.session_state['nexus_session']['transcript']['turns'] == []
    else:
        monkeypatch.setattr(isolated_ui[0], 'run_turn', lambda **kw: {'status':'answered','assistant_text':'Đã chuyển chủ đề.','rounds':[],'tool_events':[]})
        submit(page, 'Chuyển chủ đề')
        assert page.session_state['nexus_session']['transcript']['turns'][0]['send_confirmation']['status'] == 'superseded_by_new_message'
    assert not page.exception
    assert sends == []
    assert not any(x.label == 'Xác nhận gửi Telegram' for x in page.button)


def test_ui_keeps_comparison_sources_if_synthesis_fails(isolated_ui, monkeypatch):
    fake_chat(monkeypatch, isolated_ui[0], {'status':'provider_error','assistant_text':'synthesis unavailable', 'rounds':[],
        'tool_events':[{'tool':'compare_research','result':{'status':'partial','covered_cells':1,'total_cells':2,
            'sources':[{'id':'S1','url':'https://example.com/evidence','title':'Evidence'}],
            'cells':[{'evidence':[{'source_id':'S1','excerpt':'The source excerpt belongs to this matrix cell.'}]}]}}]})
    page = open_app()
    submit(page, 'So sánh')
    assert any('synthesis unavailable' in x.value for x in page.error)
    assert any('1/2 ô có nguồn' in x.value for x in page.warning)
    assert any('The source excerpt belongs to this matrix cell.' in x.value for x in page.markdown)
    assert any('https://example.com/evidence' in x.value for x in page.markdown)


@pytest.mark.parametrize('provider_name,key', [('openrouter','OPENROUTER_API_KEY'), ('groq','GROQ_API_KEY')])
def test_same_application_routes_all_tools_through_selected_provider(isolated_ui, monkeypatch, provider_name, key):
    import providers
    from providers.base import ModelResponse
    monkeypatch.setenv(key, 'offline-selected-provider-key')
    recorded, constructed = [], []
    class Provider:
        def complete(self, messages, tools, **kwargs):
            recorded.append((messages, tools, kwargs))
            return ModelResponse(text='Đã sẵn sàng nghiên cứu.')
    def make(name):
        constructed.append(name)
        return Provider()
    monkeypatch.setattr(providers, 'make_provider', make)
    page = open_app()
    assert constructed == []
    assert next(x for x in page.selectbox if x.key == 'selected_provider').value == provider_name
    submit(page, 'Bạn hỗ trợ nghiên cứu gì?')
    assert constructed == [provider_name]
    names = {tool['function']['name'] for tool in recorded[0][1]}
    assert len(names) == 15
    assert {'investigate','compare_research','citation_audit','deduplicate','research_board'} <= names
    transcript = page.session_state['nexus_session']['transcript']
    assert transcript['provider'] == provider_name
    assert len(transcript['turns']) == 1
    assert transcript['turns'][0]['model_requests'][0]['messages'] == recorded[0][0]
    assert any('Research board' in x.label for x in page.tabs)
