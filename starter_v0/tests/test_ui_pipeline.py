"""Offline evidence that pipeline views describe requests and actions that occurred."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from providers.base import ModelResponse, ToolCall
from ui.runtime import redact, run_turn


class RecordedProvider:
    def __init__(self, *responses: ModelResponse | Exception):
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def complete(self, messages, tools, **kwargs):
        self.calls.append({"messages": copy.deepcopy(messages), "tools": copy.deepcopy(tools), **kwargs})
        if not self.responses:
            raise AssertionError("Unexpected extra model request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def invoke(provider, **overrides):
    options = {"provider": provider, "messages": [{"role": "user", "content": "Find sources."}],
               "tools": [], "model": "offline-model", "executors": {}}
    options.update(overrides)
    return run_turn(**options)


def test_recorded_payload_preserves_input_order_and_detaches_configuration_snapshot():
    messages = [
        {"role": "system", "content": "Lab system prompt."},
        {"role": "system", "content": "Public deployment policy."},
        {"role": "user", "content": "Previous question."},
        {"role": "assistant", "content": "Previous answer."},
        {"role": "user", "content": "New research question."},
    ]
    schema = [{"type": "function", "function": {"name": "lookup", "description": "Find source URLs.",
               "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}}}]
    original_messages, original_schema = copy.deepcopy(messages), copy.deepcopy(schema)
    provider = RecordedProvider(ModelResponse(text="A final answer."))

    result = invoke(provider, messages=messages, tools=schema)

    assert result["model_requests"][0]["messages"] == provider.calls[0]["messages"] == original_messages
    assert result["model_requests"][0]["status"] == "response_received"
    assert result["model_requests"][0]["tool_calls_returned"] == 0
    assert result["request_config"] == {"model": "offline-model", "temperature": 0.0,
                                         "max_tool_rounds": 4, "max_tool_calls": 8, "tools": original_schema}
    assert result["model_requests"][0]["model"] == provider.calls[0]["model"] == "offline-model"
    assert result["model_requests"][0]["temperature"] == provider.calls[0]["temperature"] == 0.0
    messages[0]["content"] = "Changed later."
    schema[0]["function"]["parameters"]["properties"]["query"]["type"] = "number"
    assert result["model_requests"][0]["messages"] == original_messages
    assert result["request_config"]["tools"] == original_schema


def test_tool_feedback_trace_matches_bounded_model_transport_and_retains_full_tool_output():
    board = {"status": "ok", "items": [{"title": "Long source", "url": "https://example.test/source",
             "summary": "source excerpt " * 4000}], "stats": {"unique_item_count": 1}}
    provider = RecordedProvider(
        ModelResponse(tool_calls=[ToolCall("research_board", {"query": "batteries"})]),
        ModelResponse(text="One source was returned."),
    )

    result = invoke(provider, executors={"research_board": lambda **args: board})

    assert len(provider.calls) == len(result["model_requests"]) == 2
    assert [request["messages"] for request in result["model_requests"]] == [call["messages"] for call in provider.calls]
    feedback = result["model_requests"][1]["messages"][-1]
    assert feedback["role"] == "user"
    assert feedback["content"].startswith("TOOL_RESULTS_JSON:\n")
    assert '"truncated_for_model": true' in feedback["content"]
    assert len(feedback["content"]) < 24500
    assert len(result["tool_events"][0]["result"]["items"][0]["summary"]) > 24000
    assert result["tool_events"][0]["result"] == board
    assert result["model_requests"][1]["messages"][-2]["role"] == "assistant"
    assert "TOOL_CALLS_JSON:" in result["model_requests"][1]["messages"][-2]["content"]


def test_recorded_request_contains_actual_context_budget_instead_of_unbounded_history():
    messages = [{"role": "system", "content": "Lab prompt."},
                {"role": "system", "content": "Public policy."},
                {"role": "user", "content": "old-history " * 7000},
                {"role": "assistant", "content": "Previous answer."},
                {"role": "user", "content": "Latest question."}]
    provider = RecordedProvider(ModelResponse(text="Done."))

    result = invoke(provider, messages=messages)

    actual = result["model_requests"][0]["messages"]
    assert actual == provider.calls[0]["messages"]
    assert sum(len(message["content"]) for message in actual) <= 64000
    assert [message["content"] for message in actual[:2]] == ["Lab prompt.", "Public policy."]
    assert actual[-1]["content"] == "Latest question."
    assert not any("old-history" in message["content"] for message in actual)
    assert any("old-history" in message["content"] for message in result["messages"])


def test_clarify_pipeline_records_proposed_but_unexecuted_calls_and_does_not_invent_second_request():
    calls = []
    provider = RecordedProvider(ModelResponse(tool_calls=[
        ToolCall("clarify", {"question": "Which URL?"}),
        ToolCall("fetch", {"url": "https://invented.test"}),
    ]))

    result = invoke(provider, executors={"clarify": lambda **args: {"awaiting_user": True, **args},
                                       "fetch": lambda **args: calls.append(args)})

    assert result["status"] == "waiting_for_user"
    assert len(result["model_requests"]) == len(provider.calls) == 1
    assert result["model_requests"][0]["tool_calls_returned"] == 2
    assert [call["name"] for call in result["rounds"][0]["tool_calls"]] == ["clarify", "fetch"]
    assert [event["tool"] for event in result["tool_events"]] == ["clarify"]
    assert calls == []


def test_provider_failure_keeps_attempted_payload_without_fabricating_a_response():
    class QuotaError(RuntimeError):
        status_code = 429

    provider = RecordedProvider(QuotaError("Private upstream quota detail."))

    result = invoke(provider)

    assert result["status"] == "provider_error"
    assert result["rounds"] == result["tool_events"] == []
    assert len(result["model_requests"]) == 1
    attempted = result["model_requests"][0]
    assert attempted["status"] == "provider_error"
    assert attempted["messages"] == provider.calls[0]["messages"]
    assert attempted["error"]["http_status"] == 429
    assert "tool_calls_returned" not in attempted
    assert "Private upstream quota detail" not in json.dumps(result)


def test_new_pipeline_metadata_redacts_prompt_schema_and_tool_feedback():
    secret = "offline-only-pipeline-private-key-8921"
    schema = [{"type": "function", "function": {"name": "lookup", "description": f"Secret is {secret}",
               "parameters": {"type": "object", "properties": {}}}}]
    provider = RecordedProvider(ModelResponse(tool_calls=[ToolCall("lookup", {"query": secret})]),
                                ModelResponse(text="Done."))

    result = invoke(provider, messages=[{"role": "system", "content": f"Prompt {secret}"}], tools=schema,
                    executors={"lookup": lambda **args: {"api_key": secret, "snippet": secret}}, secrets=[secret])

    assert secret not in json.dumps(result)
    assert result["request_config"]["tools"] == redact(schema, [secret])
    assert result["model_requests"][0]["messages"] == provider.calls[0]["messages"]
    assert "[REDACTED]" in result["model_requests"][0]["messages"][0]["content"]
    assert "[REDACTED]" in result["model_requests"][1]["messages"][-1]["content"]


def test_trace_view_marks_unexecuted_proposals_and_direct_form_model_bypass():
    from ui.pipeline import trace_stages

    agent = {"interaction": "agent_chat", "status": "waiting_for_user", "user": "Read that article.",
             "rounds": [{"round": 1, "tool_calls": [{"name": "clarify", "args": {}},
                          {"name": "fetch", "args": {}}], "tool_results": [{"tool": "clarify", "args": {},
                          "result": {"awaiting_user": True, "question": "Which URL?"}}]}],
             "tool_events": [{"tool": "clarify", "args": {},
                              "result": {"awaiting_user": True, "question": "Which URL?"}}]}

    stages = trace_stages(agent)
    assert any(stage["status"] == "waiting" for stage in stages)
    assert any(stage["status"] == "not_executed" and "fetch" in json.dumps(stage) for stage in stages)
    direct = trace_stages({"interaction": "explicit_board_form", "status": "empty", "user": "Research desk",
                           "rounds": [], "tool_events": [{"tool": "research_board", "args": {},
                                                          "result": {"status": "empty"}}]})
    rendered = json.dumps(direct, ensure_ascii=False).lower()
    assert "research_board" in rendered
    assert "model" in rendered
    assert any(token in rendered for token in ("không gọi", "không được gọi", "bypass"))


def test_trace_html_escapes_model_and_tool_content():
    from ui.pipeline import trace_html

    attack = '<script>alert("pipeline")</script><img src=x onerror=alert(1)>'
    document = trace_html([{"label": attack, "detail": attack, "status": "error"}])

    assert "<script>alert" not in document
    assert "<img src=x" not in document
    assert "&lt;script&gt;" in document
    assert "&lt;img" in document


@pytest.fixture
def offline_pipeline_ui(monkeypatch, tmp_path):
    import socket
    import providers
    import requests
    from streamlit.testing.v1 import AppTest

    env = tmp_path / "empty.env"
    env.write_text("", encoding="utf-8")
    monkeypatch.setenv("DAY03_ENV_FILE", str(env))
    monkeypatch.setenv("NEXUS_TRANSCRIPTS_DIR", str(tmp_path / "transcripts"))
    monkeypatch.setenv("NEXUS_MODEL", "offline-model")
    for name in ("GROQ_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY",
                 "GEMINI_API_KEY", "GOOGLE_API_KEY", "TAVILY_API_KEY", "FIRECRAWL_API_KEY",
                 "RAPIDAPI_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "offline-configured-groq-pipeline-key")
    forbidden = []

    def no_network(*args, **kwargs):
        forbidden.append("provider_or_http")
        raise AssertionError("Pipeline inspection attempted external I/O")

    monkeypatch.setattr(providers, "make_provider", no_network)
    monkeypatch.setattr(requests.Session, "request", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    return {"AppTest": AppTest, "providers": providers, "forbidden": forbidden,
            "root": Path(__file__).resolve().parents[1], "transcripts": tmp_path / "transcripts"}


def test_initial_pipeline_exposes_lab_configuration_without_running_a_request(offline_pipeline_ui):
    ui = offline_pipeline_ui
    app = ui["AppTest"].from_file(str(ui["root"] / "app.py")).run(timeout=25)

    assert not app.exception
    assert any("Pipeline" in tab.label for tab in app.tabs)
    prompt = (ui["root"] / "artifacts/system_prompt.md").read_text(encoding="utf-8")
    # st.code normalizes surrounding whitespace while rendering its source text.
    assert any(code.value.strip() == prompt.strip() for code in app.code)
    assert any("Deployment policy for this public UI" in code.value for code in app.code)
    assert any("research_board" in str(node.value) for node in app.json)
    assert ui["forbidden"] == []
    assert not ui["transcripts"].exists()


def test_inspecting_two_recorded_turns_preserves_exact_payload_and_makes_no_new_calls(offline_pipeline_ui, monkeypatch):
    ui = offline_pipeline_ui
    provider = RecordedProvider(ModelResponse(text="I can help research sources."),
                                ModelResponse(tool_calls=[ToolCall("clarify", {"question": "Which URL?",
                                                                           "response_type": "text"})]))
    constructed = []

    def local_provider(name):
        constructed.append(name)
        return provider

    monkeypatch.setattr(ui["providers"], "make_provider", local_provider)
    app = ui["AppTest"].from_file(str(ui["root"] / "app.py")).run(timeout=25)
    for question in ("What can you help research?", "Read that article."):
        next(widget for widget in app.text_area if widget.key == "chat_draft").input(question)
        next(button for button in app.button if button.label.startswith("Gửi yêu cầu")).click().run(timeout=25)
        assert not app.exception

    assert constructed == ["groq", "groq"]
    assert len(provider.calls) == 2
    turns = app.session_state["nexus_session"]["transcript"]["turns"]
    assert turns[1]["status"] == "waiting_for_user"
    assert turns[1]["model_requests"][0]["messages"] == provider.calls[1]["messages"]
    selector = next(widget for widget in app.selectbox if widget.key == "pipeline_turn_index")
    selector.select(0).run(timeout=25)
    assert not app.exception
    selector = next(widget for widget in app.selectbox if widget.key == "pipeline_turn_index")
    selector.select(1).run(timeout=25)
    assert not app.exception
    assert constructed == ["groq", "groq"]
    assert len(provider.calls) == 2
    assert ui["forbidden"] == []
    saved = list(ui["transcripts"].glob("*.transcript.json"))
    assert len(saved) == 1
    recorded = json.loads(saved[0].read_text(encoding="utf-8"))
    assert recorded["turns"][1]["model_requests"][0]["messages"] == provider.calls[1]["messages"]


def test_new_turn_selects_latest_pipeline_and_session_reset_removes_old_selection(offline_pipeline_ui, monkeypatch):
    ui = offline_pipeline_ui
    provider = RecordedProvider(*(ModelResponse(text=f"Offline answer {number}.") for number in range(1, 5)))
    constructed = []

    def local_provider(name):
        constructed.append(name)
        return provider

    monkeypatch.setattr(ui["providers"], "make_provider", local_provider)
    app = ui["AppTest"].from_file(str(ui["root"] / "app.py")).run(timeout=25)

    def submit(question):
        next(widget for widget in app.text_area if widget.key == "chat_draft").input(question)
        next(button for button in app.button if button.label.startswith("Gửi yêu cầu")).click().run(timeout=25)
        assert not app.exception

    for question in ("First old question.", "Second old question."):
        submit(question)
    selector = next(widget for widget in app.selectbox if widget.key == "pipeline_turn_index")
    assert selector.value == 1
    selector.select(0).run(timeout=25)
    assert not app.exception
    assert next(widget for widget in app.selectbox if widget.key == "pipeline_turn_index").value == 0
    assert len(provider.calls) == 2

    submit("Third question should become the selected trace.")

    assert next(widget for widget in app.selectbox if widget.key == "pipeline_turn_index").value == 2
    previous_session = app.session_state["nexus_session"]["transcript"]["transcript_id"]
    next(button for button in app.button if "Phiên mới" in button.label).click().run(timeout=25)
    assert not app.exception
    session = app.session_state["nexus_session"]
    assert session["transcript"]["transcript_id"] != previous_session
    assert session["transcript"]["turns"] == []
    assert not any(widget.key == "pipeline_turn_index" for widget in app.selectbox)
    assert "pipeline_turn_index" not in app.session_state
    assert "pipeline_seen_turn_count" not in app.session_state
    assert len(provider.calls) == 3

    submit("Fresh session question.")

    assert next(widget for widget in app.selectbox if widget.key == "pipeline_turn_index").value == 0
    turns = app.session_state["nexus_session"]["transcript"]["turns"]
    assert len(turns) == turns[0]["turn_index"] == 1
    assert turns[0]["user"] == "Fresh session question."
    assert len(provider.calls[3]["messages"]) == 3
    assert provider.calls[3]["messages"][-1] == {"role": "user", "content": "Fresh session question."}
    assert constructed == ["groq"] * 4
    assert len(provider.calls) == 4
    assert ui["forbidden"] == []
