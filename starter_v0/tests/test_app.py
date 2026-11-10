"""Offline smoke checks for the real Streamlit UI and its user boundaries."""
from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def isolated_ui(monkeypatch, tmp_path):
    # The application deliberately reads .env on startup; redirect to an empty file.
    empty_env = tmp_path / "empty.env"
    empty_env.write_text("", encoding="utf-8")
    monkeypatch.setenv("DAY03_ENV_FILE", str(empty_env))
    for name in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY",
                 "TAVILY_API_KEY", "FIRECRAWL_API_KEY", "RAPIDAPI_KEY", "TELEGRAM_BOT_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    import chat

    saved = []
    monkeypatch.setattr(chat, "write_transcript", lambda path, transcript: saved.append(transcript))
    return saved


def test_ui_opens_without_credentials_or_network(isolated_ui, monkeypatch):
    import chat

    def unexpected_call(**kwargs):
        raise AssertionError("No provider call is allowed before a user message")

    monkeypatch.setattr(chat, "run_model_tool_loop", unexpected_call)
    page = AppTest.from_file(str(APP_PATH)).run(timeout=15)
    assert not page.exception
    assert page.chat_input[0].disabled
    assert any("OPENAI_API_KEY" in item.value for item in page.warning)
    assert any("So sánh có bằng chứng" in item.label for item in page.button)
    assert any("Kiểm tra trích dẫn" in item.label for item in page.button)
    assert not isolated_ui


def test_ui_chat_records_real_loop_result_and_shows_tool_failures(isolated_ui, monkeypatch):
    import chat

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key-for-offline-ui")
    requests = []

    def fake_loop(**kwargs):
        requests.append(kwargs)
        return {"status": "answered", "assistant_text": "Chưa có đủ dữ liệu để kết luận.", "rounds": [],
                "tool_events": [{"tool": "lookup", "args": {"query": "RAG"},
                                 "result": {"error": "rate_limited", "message": "HTTP 429"}}]}

    monkeypatch.setattr(chat, "run_model_tool_loop", fake_loop)
    page = AppTest.from_file(str(APP_PATH)).run(timeout=15)
    assert not page.exception
    page.chat_input[0].set_value("Nghiên cứu RAG").run(timeout=15)
    assert not page.exception
    assert len(requests) == 1
    assert requests[0]["messages"][-1]["content"] == "Nghiên cứu RAG"
    assert requests[0]["model"] == "gpt-4o-mini"
    assert any("rate_limited" in item.value for item in page.warning)
    assert isolated_ui[-1]["turns"][-1]["tool_events"][0]["tool"] == "lookup"


def test_ui_requires_button_for_exact_telegram_payload(isolated_ui, monkeypatch):
    import chat

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key-for-offline-ui")
    draft = "Bản nghiên cứu đã duyệt — có nguồn."
    monkeypatch.setattr(chat, "run_model_tool_loop", lambda **kwargs: {
        "status": "waiting_for_user", "assistant_text": "Bạn xác nhận nội dung gửi nhé.",
        "rounds": [], "tool_events": [], "pending_send": {"text": draft},
    })
    sends = []

    def fake_send(call, **kwargs):
        sends.append((call, kwargs))
        return {"tool": "send", "args": call.args, "result": {"status": "sent"}}

    monkeypatch.setattr(chat, "execute_tool_call", fake_send)
    page = AppTest.from_file(str(APP_PATH)).run(timeout=15)
    page.chat_input[0].set_value("Gửi bản nghiên cứu lên Telegram").run(timeout=15)
    assert not page.exception
    assert sends == []
    assert any(item.value == draft for item in page.code)
    button = next(item for item in page.button if item.label == "Xác nhận gửi Telegram")
    button.click().run(timeout=15)
    assert not page.exception
    assert len(sends) == 1
    assert sends[0][0].args == {"text": draft, "confirmed": True}
    assert sends[0][1] == {"confirmed_send_text": draft}


def test_ui_redacts_credentials_and_filters_unsafe_source_links(isolated_ui, monkeypatch):
    from app import extract_sources, redact

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "very-secret-token")
    assert redact({"error": "request to /very-secret-token/send", "api_key": "hidden"}) == {
        "error": "request to /[REDACTED]/send", "api_key": "[REDACTED]"}
    sources = extract_sources([{"result": {"sources": [
        {"url": "javascript:alert(1)", "title": "bad"},
        {"url": "https://example.com/paper", "title": "Paper", "excerpts": [{"text": "Evidence"}]},
        {"url": "https://example.com/paper", "title": "Duplicate"},
        {"url": "https://user:password@example.org/private", "title": "Credentials in URL"},
    ]}}])
    assert len(sources) == 1
    assert sources[0]["title"] == "Paper"
    assert sources[0]["excerpt"] == "Evidence"


@pytest.mark.parametrize("action", ["cancel", "new_message", "new_session"])
def test_pending_send_expires_when_user_moves_on(isolated_ui, monkeypatch, action):
    import chat

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key-for-offline-ui")
    responses = iter([
        {"status": "waiting_for_user", "assistant_text": "Bạn kiểm tra bản nháp nhé.",
         "rounds": [], "tool_events": [], "pending_send": {"text": "Bản nháp cũ"}},
        {"status": "provider_error", "assistant_text": "", "error": "synthesis unavailable",
         "rounds": [], "tool_events": []},
    ])
    monkeypatch.setattr(chat, "run_model_tool_loop", lambda **kwargs: next(responses))
    sends = []
    monkeypatch.setattr(chat, "execute_tool_call", lambda *args, **kwargs: sends.append(args))
    page = AppTest.from_file(str(APP_PATH)).run(timeout=15)
    page.chat_input[0].set_value("Chuẩn bị gửi Telegram").run(timeout=15)
    assert any(item.label == "Xác nhận gửi Telegram" for item in page.button)
    if action == "cancel":
        next(item for item in page.button if item.label == "Hủy gửi").click().run(timeout=15)
        assert isolated_ui[-1]["turns"][0]["send_confirmation"]["status"] == "cancelled"
    elif action == "new_session":
        next(item for item in page.button if item.label == "＋ Cuộc trò chuyện mới").click().run(timeout=15)
        assert isolated_ui[-1]["turns"][0]["send_confirmation"]["status"] == "cancelled_by_new_session"
    page.chat_input[0].set_value("Chuyển sang câu hỏi khác").run(timeout=15)
    assert not page.exception
    assert not any(item.label == "Xác nhận gửi Telegram" for item in page.button)
    assert sends == []
    if action == "new_message":
        assert isolated_ui[-1]["turns"][0]["send_confirmation"]["status"] == "superseded_by_new_message"


def test_ui_keeps_comparison_sources_if_synthesis_fails(isolated_ui, monkeypatch):
    import chat

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key-for-offline-ui")
    monkeypatch.setattr(chat, "run_model_tool_loop", lambda **kwargs: {
        "status": "provider_error", "assistant_text": "", "error": "synthesis unavailable", "rounds": [],
        "tool_events": [{"tool": "compare_research", "args": {}, "result": {
            "status": "partial", "covered_cells": 1, "total_cells": 2,
            "sources": [{"id": "S1", "url": "https://example.com/evidence", "title": "Comparison evidence"}],
            "cells": [{"evidence": [{"source_id": "S1", "excerpt": "The source excerpt belongs to this matrix cell."}]}],
        }}],
    })
    page = AppTest.from_file(str(APP_PATH)).run(timeout=15)
    page.chat_input[0].set_value("So sánh hai giải pháp").run(timeout=15)
    assert not page.exception
    assert any("synthesis unavailable" in item.value for item in page.error)
    assert any("1/2 ô có nguồn" in item.value for item in page.warning)
    assert any("The source excerpt belongs to this matrix cell." in item.value for item in page.markdown)
    assert any("https://example.com/evidence" in item.value for item in page.markdown)
