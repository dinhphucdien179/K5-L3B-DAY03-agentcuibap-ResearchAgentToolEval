"""Offline behavioral checks for the public UI's real orchestration boundary."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from providers.base import ModelResponse, ToolCall
from ui.runtime import execute_tool, redact, run_turn


class ScriptedProvider:
    """A deterministic model substitute; no SDK or HTTP client is constructed."""

    def __init__(self, *responses: ModelResponse | Exception) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def complete(self, messages, tools, **kwargs):
        self.calls.append({"messages": copy.deepcopy(messages), "tools": copy.deepcopy(tools), **kwargs})
        if not self.responses:
            raise AssertionError("The runtime called the provider beyond the scripted boundary")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _run(provider: ScriptedProvider, **kwargs) -> dict[str, Any]:
    options = {
        "provider": provider,
        "messages": [{"role": "user", "content": "Research battery recycling."}],
        "tools": [],
        "max_tool_rounds": 4,
        "executors": {},
    }
    options.update(kwargs)
    return run_turn(**options)


def test_redaction_preserves_structure_and_unknown_data_without_mutating_input():
    secret = "test-only-private-credential-9f26"
    source = {
        "assistant_text": f"Provider failed using {secret}",
        "nested": [{"api_key": "another-private-value", "item_ids": None, "count": 0}],
        "url": f"https://api.example.test/search?api_key={secret}&q=batteries",
        "title": "Source coverage",
    }
    original = copy.deepcopy(source)

    safe = redact(source, secrets=[secret])

    serialized = json.dumps(safe)
    assert secret not in serialized
    assert "another-private-value" not in serialized
    assert safe["nested"][0]["item_ids"] is None
    assert safe["nested"][0]["count"] == 0
    assert safe["title"] == "Source coverage"
    assert source == original


@pytest.mark.parametrize("confirmed", [False, True])
def test_public_demo_blocks_send_before_the_delivery_executor(confirmed):
    deliveries = []

    def delivery(**args):
        deliveries.append(args)
        return {"status": "sent"}

    event = execute_tool(
        ToolCall("send", {"text": "A reviewed draft", "confirmed": confirmed}),
        executors={"send": delivery},
    )

    assert deliveries == []
    assert event["tool"] == "send"
    assert event["result"]["status"] == "blocked"
    assert event["result"].get("message")


def test_blocked_delivery_ends_the_turn_and_cannot_be_rewritten_as_sent():
    deliveries = []
    provider = ScriptedProvider(
        ModelResponse(tool_calls=[ToolCall("send", {"text": "Reviewed draft", "confirmed": True})]),
        ModelResponse(text="The draft was sent."),
    )

    result = _run(provider, executors={"send": lambda **args: deliveries.append(args)})

    assert result["status"] == "blocked"
    assert len(provider.calls) == 1
    assert deliveries == []
    assert result["tool_events"][0]["result"]["side_effect_performed"] is False
    assert result["assistant_text"] == result["tool_events"][0]["result"]["message"]
    assert "The draft was sent." not in json.dumps(result)


@pytest.mark.parametrize("args", [None, "{not-json}", [], 17])
def test_malformed_model_arguments_are_reported_without_running_the_tool(args):
    invocations = []

    def lookup(**values):
        invocations.append(values)
        return {"items": []}

    event = execute_tool(ToolCall("lookup", args), executors={"lookup": lookup})

    assert invocations == []
    assert event["result"].get("error")
    assert event["result"].get("message")


def test_unknown_tool_is_visible_instead_of_becoming_success():
    event = execute_tool(ToolCall("undeclared_tool", {}), executors={})

    assert event["tool"] == "undeclared_tool"
    assert event["result"].get("error")
    assert event["result"].get("message")


def test_tool_exception_is_visible_and_configured_secret_is_removed():
    secret = "offline-tool-secret-42"

    def broken(**args):
        raise ValueError(f"Invalid provider payload; credential={secret}")

    event = execute_tool(
        ToolCall("lookup", {"query": "battery recycling"}),
        executors={"lookup": broken},
        secrets=[secret],
    )

    assert event["result"]["error"] == "ValueError"
    assert event["result"].get("message")
    assert secret not in json.dumps(event)


def test_provider_exception_becomes_a_visible_redacted_turn():
    secret = "offline-provider-secret-73"
    provider = ScriptedProvider(RuntimeError(f"Provider rate limit; auth={secret}"))

    result = _run(provider, secrets=[secret])

    assert len(provider.calls) == 1
    assert result["status"] == "provider_error"
    assert result["error"]["type"] == "RuntimeError"
    assert result["error"].get("message")
    assert secret not in json.dumps(result)
    assert result["tool_events"] == []


def test_clarification_pauses_before_later_calls_and_keeps_the_question_in_history():
    question = "Which account should I research?"
    lookups = []

    def clarify(**args):
        return {"awaiting_user": True, **args}

    provider = ScriptedProvider(ModelResponse(tool_calls=[
        ToolCall("clarify", {"question": question, "response_type": "text"}),
        ToolCall("lookup", {"query": "an invented account"}),
    ]))
    incoming = [{"role": "user", "content": "Summarize that account."}]
    original = copy.deepcopy(incoming)

    result = _run(
        provider,
        messages=incoming,
        executors={"clarify": clarify, "lookup": lambda **args: lookups.append(args)},
    )

    assert result["status"] == "waiting_for_user"
    assert result["assistant_text"] == question
    assert len(provider.calls) == 1
    assert lookups == []
    assert [event["tool"] for event in result["tool_events"]] == ["clarify"]
    history = json.dumps(result["messages"])
    assert question in history
    assert "response_type" in history
    assert incoming == original


def test_a_followup_answer_uses_the_saved_clarification_context():
    question = "Which topic should I research?"
    first = _run(
        ScriptedProvider(ModelResponse(tool_calls=[ToolCall("clarify", {
            "question": question, "response_type": "text",
        })])),
        executors={"clarify": lambda **args: {"awaiting_user": True, **args}},
    )
    followup = ScriptedProvider(
        ModelResponse(tool_calls=[ToolCall("lookup", {"query": "battery recycling"})]),
        ModelResponse(text="Found a source: https://example.test/batteries"),
    )
    source = {"items": [{"title": "Battery recycling", "url": "https://example.test/batteries"}]}

    result = _run(
        followup,
        messages=[*first["messages"], {"role": "user", "content": "battery recycling"}],
        executors={"lookup": lambda **args: source},
    )

    assert result["status"] == "answered"
    assert len(followup.calls) == 2
    assert question in json.dumps(followup.calls[0]["messages"])
    assert followup.calls[0]["messages"][-1]["content"] == "battery recycling"
    assert "https://example.test/batteries" in json.dumps(followup.calls[1]["messages"])
    assert result["tool_events"][0]["args"] == {"query": "battery recycling"}
    assert result["tool_events"][0]["result"] == source


def test_partial_board_preserves_unknown_coverage_and_returned_errors():
    board = {
        "tool": "research_board", "status": "partial", "items": [],
        "comparison": {
            "queries": [
                {"id": "q1", "status": "empty", "item_ids": [], "retrieved_count": 0},
                {"id": "q2", "status": "error", "item_ids": None, "retrieved_count": None,
                 "error": {"error": "HTTPError", "http_status": 429}},
                {"id": "q3", "status": "skipped", "item_ids": None, "retrieved_count": None},
            ],
            "pairwise": [{"status": "incomplete", "shared_item_ids": None}],
        },
    }
    provider = ScriptedProvider(
        ModelResponse(tool_calls=[ToolCall("research_board", {"query": "batteries"})]),
        ModelResponse(text="The board is partial because a query was rate limited."),
    )

    result = _run(provider, executors={"research_board": lambda **args: board})

    visible = result["tool_events"][0]["result"]
    assert visible["status"] == "partial"
    assert visible["comparison"]["queries"][0]["item_ids"] == []
    assert visible["comparison"]["queries"][1]["item_ids"] is None
    assert visible["comparison"]["queries"][2]["retrieved_count"] is None
    assert visible["comparison"]["queries"][1]["error"]["http_status"] == 429
    assert visible["comparison"]["pairwise"][0]["shared_item_ids"] is None
    assert "429" in json.dumps(provider.calls[1]["messages"])


def test_returned_tool_error_remains_visible_after_the_model_answers():
    failure = {"status": "error", "error": "HTTPError", "http_status": 429, "retryable": True}
    provider = ScriptedProvider(
        ModelResponse(tool_calls=[ToolCall("lookup", {"query": "batteries"})]),
        ModelResponse(text="Search is rate limited; please try later."),
    )

    result = _run(provider, executors={"lookup": lambda **args: failure})

    assert result["status"] == "answered"
    assert result["tool_events"][0]["result"] == failure
    assert "HTTPError" in json.dumps(provider.calls[1]["messages"])


def test_all_returned_turn_data_redacts_secrets_from_model_args_and_tool_results():
    secret = "offline-secret-in-every-boundary-a15"
    provider = ScriptedProvider(
        ModelResponse(text=f"I saw {secret}", tool_calls=[ToolCall("lookup", {"query": secret})]),
        ModelResponse(text=f"Final answer {secret}"),
    )
    source = {"items": [], "debug": f"credential={secret}"}

    result = _run(provider, executors={"lookup": lambda **args: source}, secrets=[secret])

    assert secret not in json.dumps(result)
    assert result["tool_events"][0]["args"]["query"] != secret
    assert result["assistant_text"] != f"Final answer {secret}"
    assert result["status"] == "answered"


def test_repeated_tool_selection_stops_at_the_configured_round_limit():
    invocations = []
    provider = ScriptedProvider(*[
        ModelResponse(tool_calls=[ToolCall("lookup", {"query": "batteries"})]) for _ in range(3)
    ])

    result = _run(
        provider, max_tool_rounds=3,
        executors={"lookup": lambda **args: invocations.append(args) or {"items": []}},
    )

    assert result["status"] == "max_tool_rounds"
    assert len(provider.calls) == 3
    assert len(invocations) == 3
    assert len(result["tool_events"]) == 3


def test_tool_call_budget_is_shared_across_rounds_and_stops_actual_execution():
    invocations = []
    provider = ScriptedProvider(*[
        ModelResponse(tool_calls=[ToolCall("lookup", {"query": f"topic-{i}"}) for i in range(start, start + 5)])
        for start in (0, 5)
    ])

    result = _run(
        provider, executors={"lookup": lambda **args: invocations.append(args["query"]) or {"items": []}},
    )

    assert result["status"] == "max_tool_calls"
    assert len(provider.calls) == 2
    assert invocations == [f"topic-{i}" for i in range(8)]
    assert len(result["tool_events"]) == 8
    assert "topic-8" not in [event["args"]["query"] for event in result["tool_events"]]


def test_large_board_is_compacted_for_model_while_full_raw_trace_is_retained():
    board = {
        "status": "partial",
        "items": [{
            "id": f"i{i}", "title": f"Source {i}", "url": f"https://example.test/article-{i}",
            "source": "example.test", "summary": ("x" * 1200) + f"-full-excerpt-tail-{i}",
        } for i in range(60)],
        "comparison": {"queries": [{
            "query": "failed query", "status": "error", "retrieved_count": None,
            "error": {"error": "HTTPError", "http_status": 429},
        }]},
        "warnings": ["Coverage is partial."],
    }
    provider = ScriptedProvider(
        ModelResponse(tool_calls=[ToolCall("research_board", {"query": "batteries"})]),
        ModelResponse(text="Available evidence is partial."),
    )

    result = _run(provider, executors={"research_board": lambda **args: board})

    transport = provider.calls[1]["messages"]
    transport_text = json.dumps(transport)
    assert result["status"] == "answered"
    assert sum(len(message["content"]) for message in transport) <= 64000
    assert "truncated_for_model" in transport_text
    assert "full-excerpt-tail-59" not in transport_text
    assert "429" in transport_text
    assert result["tool_events"][0]["result"] == board
    assert result["rounds"][0]["tool_results"][0]["result"]["items"][-1]["summary"].endswith("full-excerpt-tail-59")


def test_context_budget_keeps_system_policy_and_latest_request():
    prefix = [{"role": "system", "content": "Research scope."}, {"role": "system", "content": "Delivery is blocked."}]
    history = [{"role": "assistant", "content": str(i) * 10000} for i in range(10)]
    latest = {"role": "user", "content": "Read the latest available board."}
    provider = ScriptedProvider(ModelResponse(text="Ready."))

    _run(provider, messages=[*prefix, *history, latest])

    actual = provider.calls[0]["messages"]
    assert actual[:2] == prefix
    assert actual[-1] == latest
    assert sum(len(message["content"]) for message in actual) <= 64000
    assert len(actual) < len(prefix) + len(history) + 1


def test_oversized_last_message_is_bounded_for_provider_but_not_lost_from_trace():
    oversized = {"role": "user", "content": "TOOL_RESULTS_JSON: " + ("large-result " * 10000)}
    policy = {"role": "system", "content": "Delivery is blocked."}
    provider = ScriptedProvider(ModelResponse(text="The result exceeded the context budget."))

    result = _run(provider, messages=[policy, oversized])

    sent = provider.calls[0]["messages"]
    assert sent[0] == policy
    assert sum(len(message["content"]) for message in sent) <= 64000
    assert len(sent[-1]["content"]) < len(oversized["content"])
    assert "truncated" in sent[-1]["content"].lower()
    assert result["messages"][-2] == oversized


def test_provider_http_status_is_visible_without_echoing_exception_credentials():
    class RateLimited(RuntimeError):
        status_code = 429

    provider = ScriptedProvider(RateLimited("Authorization: private-value-never-display"))

    result = _run(provider)

    assert result["status"] == "provider_error"
    assert result["error"]["http_status"] == 429
    assert "private-value-never-display" not in json.dumps(result)


def test_paper_text_local_paths_are_redacted_but_public_source_url_remains():
    source_url = "https://arxiv.org/abs/2401.12345"
    output = {
        "pdf_path": "D:\\server\\workspace\\arxiv_papers\\2401.12345.pdf",
        "txt_path": "D:\\server\\workspace\\arxiv_papers\\2401.12345.txt",
        "message": "Downloaded D:\\server\\workspace\\arxiv_papers\\2401.12345.pdf",
        "url": source_url,
        "items": [{"url": source_url, "summary": "A public research excerpt."}],
    }

    visible = redact(output)

    assert visible["pdf_path"] != output["pdf_path"]
    assert visible["txt_path"] != output["txt_path"]
    assert "arxiv_papers" not in json.dumps(visible)
    assert visible["url"] == source_url
    assert visible["items"][0]["summary"] == "A public research excerpt."


@pytest.fixture
def offline_ui(monkeypatch, tmp_path):
    """Run the actual Streamlit script with isolated config, storage and network."""
    import socket
    import providers
    import requests
    import ui.runtime as runtime
    from streamlit.testing.v1 import AppTest

    empty_env = tmp_path / "empty.env"
    empty_env.write_text("", encoding="utf-8")
    monkeypatch.setenv("DAY03_ENV_FILE", str(empty_env))
    monkeypatch.setenv("NEXUS_TRANSCRIPTS_DIR", str(tmp_path / "transcripts"))
    monkeypatch.setenv("NEXUS_MODEL", "openai/gpt-oss-20b")
    for name in (
        "GROQ_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY", "GOOGLE_API_KEY", "TAVILY_API_KEY", "FIRECRAWL_API_KEY",
        "RAPIDAPI_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "offline-only-configured-tavily-key")
    monkeypatch.setenv("GROQ_API_KEY", "offline-only-configured-groq-key")
    forbidden = []

    def no_external_request(*args, **kwargs):
        forbidden.append("provider_or_http")
        raise AssertionError("An offline UI test attempted provider construction or HTTP")

    monkeypatch.setattr(providers, "make_provider", no_external_request)
    monkeypatch.setattr(requests.Session, "request", no_external_request)
    monkeypatch.setattr(socket, "create_connection", no_external_request)
    return {
        "AppTest": AppTest, "runtime": runtime, "forbidden": forbidden,
        "path": Path(__file__).resolve().parents[1] / "app.py",
        "transcripts": tmp_path / "transcripts",
    }


def _submit_board(app, query="battery recycling"):
    app.text_input[0].input(query)
    next(button for button in app.button if "source map" in button.label).click().run(timeout=20)


def test_ui_empty_board_submission_rerenders_chat_without_provider_or_network(offline_ui, monkeypatch):
    calls = []
    board = {
        "tool": "research_board", "status": "empty", "query": "battery recycling",
        "items": [], "sources": [], "graph": {"nodes": [], "edges": []}, "workflow": [],
        "stats": {"retrieved_count": 0, "unique_item_count": 0, "source_count": 0,
                  "duplicate_count": 0, "discarded_count": 0},
        "coverage": {}, "comparison": {"request_count": 1, "queries": [], "pairwise": []},
        "warnings": [],
    }

    def fake_board(call, **kwargs):
        calls.append(copy.deepcopy(call.args))
        return {"tool": call.name, "args": call.args, "result": board}

    monkeypatch.setattr(offline_ui["runtime"], "execute_tool", fake_board)
    app = offline_ui["AppTest"].from_file(str(offline_ui["path"])).run(timeout=20)
    assert not app.exception
    assert calls == []
    assert offline_ui["forbidden"] == []
    assert not offline_ui["transcripts"].exists()

    _submit_board(app)

    assert not app.exception
    assert offline_ui["forbidden"] == []
    assert calls == [{"query": "battery recycling", "topic": "news", "timeframe": "week",
                      "max_results": 6, "compare_queries": []}]
    assert len(app.chat_message) == 2
    assert not app.error
    turn = app.session_state["nexus_session"]["transcript"]["turns"][0]
    assert turn["status"] == "empty"
    assert turn["interaction"] == "explicit_board_form"
    assert turn["tool_events"][0]["result"] == board
    saved = list(offline_ui["transcripts"].glob("*.transcript.json"))
    assert len(saved) == 1
    assert json.loads(saved[0].read_text(encoding="utf-8"))["turns"][0]["status"] == "empty"


def test_ui_board_http429_is_visible_after_rerun_and_saved_in_trace(offline_ui, monkeypatch):
    calls = []
    failure = {
        "tool": "research_board", "status": "error", "query": "battery recycling",
        "error": "HTTPError", "http_status": 429, "retryable": True,
        "message": "Search quota reached; retry later.",
    }

    def fake_board(call, **kwargs):
        calls.append(copy.deepcopy(call.args))
        return {"tool": call.name, "args": call.args, "result": failure}

    monkeypatch.setattr(offline_ui["runtime"], "execute_tool", fake_board)
    app = offline_ui["AppTest"].from_file(str(offline_ui["path"])).run(timeout=20)
    assert not app.exception
    assert calls == []
    assert offline_ui["forbidden"] == []

    _submit_board(app)

    assert not app.exception
    assert len(calls) == 1
    assert offline_ui["forbidden"] == []
    assert any("research_board" in error.value for error in app.error)
    assert any("HTTPError" in error.value for error in app.error)
    assert any(expander.label == "Xem tool trace" for expander in app.expander)
    assert any("HTTPError" in str(node.value) and "429" in str(node.value) for node in app.json)
    turn = app.session_state["nexus_session"]["transcript"]["turns"][0]
    assert turn["status"] == "tool_error"
    assert turn["tool_events"][0]["result"]["http_status"] == 429
    saved = list(offline_ui["transcripts"].glob("*.transcript.json"))
    assert len(saved) == 1
    assert json.loads(saved[0].read_text(encoding="utf-8"))["turns"][0]["tool_events"][0]["result"] == failure
