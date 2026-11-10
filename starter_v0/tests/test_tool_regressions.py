"""Offline regression tests for invalid model arguments and action boundaries."""
from __future__ import annotations

import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS


@pytest.mark.parametrize("tool, kwargs, field", [
    ("lookup", {"query": "RAG"}, "max_results"),
    ("timeline", {"screenname": "OpenAI"}, "limit"),
    ("social_search", {"query": "RAG"}, "limit"),
    ("policy", {"query": "citation"}, "top_k"),
    ("papers", {"query": "RAG"}, "max_results"),
    ("paper_text", {"arxiv_url": "2303.08774"}, "max_pages"),
    ("paper_text", {"arxiv_url": "2303.08774"}, "max_chars"),
])
@pytest.mark.parametrize("value", [-2, 0, True, 1.5, "3", None])
def test_invalid_numeric_arguments_return_error_before_network(
    monkeypatch, fake_http, tool, kwargs, field, value,
) -> None:
    for env in ("TAVILY_API_KEY", "FIRECRAWL_API_KEY", "RAPIDAPI_KEY"):
        monkeypatch.setenv(env, "fake-key")
    calls = fake_http(FakeResponse())
    result = TOOL_FUNCTIONS[tool](**(kwargs | {field: value}))
    assert result["error"] == "ValueError"
    assert result["message"] == f"{field} must be a positive integer"
    assert calls == []


@pytest.mark.parametrize("confirmed", ["false", "true", 1, [True], {"confirmed": True}, None])
def test_send_requires_literal_boolean_true(monkeypatch, fake_http, confirmed) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake-chat")
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"](text="Pending user confirmation", confirmed=confirmed)
    assert result["status"] == "needs_confirmation"
    assert calls == []


@pytest.mark.parametrize("tool, kwargs, env", [
    ("fetch", {"url": "https://example.com"}, "FIRECRAWL_API_KEY"),
    ("timeline", {"screenname": "OpenAI"}, "RAPIDAPI_KEY"),
    ("social_search", {"query": "RAG"}, "RAPIDAPI_KEY"),
])
def test_live_tools_without_key_return_error_without_network(fake_http, tool, kwargs, env) -> None:
    calls = fake_http(FakeResponse())
    result = TOOL_FUNCTIONS[tool](**kwargs)
    assert result["error"] == "RuntimeError"
    assert env in result["message"]
    assert calls == []


@pytest.mark.parametrize("tool, kwargs, env", [
    ("fetch", {"url": "https://example.com"}, "FIRECRAWL_API_KEY"),
    ("timeline", {"screenname": "OpenAI"}, "RAPIDAPI_KEY"),
    ("social_search", {"query": "RAG"}, "RAPIDAPI_KEY"),
])
@pytest.mark.parametrize("failure", [FakeResponse(status_code=429), TimeoutError("timeout")])
def test_live_tools_http_failure_is_error_dict(monkeypatch, fake_http, tool, kwargs, env, failure) -> None:
    monkeypatch.setenv(env, "fake-key")
    calls = fake_http(failure)
    result = TOOL_FUNCTIONS[tool](**kwargs)
    assert result["error"] in {"HTTPError", "TimeoutError"}
    assert len(calls) == 1


def test_papers_maps_atom_response_without_network_or_wait(monkeypatch, fake_http) -> None:
    from tools.papers import tool as papers_module

    monkeypatch.setattr(papers_module, "_rate_limit_arxiv", lambda: None)
    calls = fake_http(FakeResponse(text='''
        <feed xmlns="http://www.w3.org/2005/Atom"
              xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
          <opensearch:totalResults>1</opensearch:totalResults>
          <entry>
            <id>https://arxiv.org/abs/2303.08774</id>
            <title>Example paper</title><summary>Evidence\n summary</summary>
            <author><name>Example Author</name></author>
            <link title="pdf" href="https://arxiv.org/pdf/2303.08774.pdf"/>
          </entry>
        </feed>'''))
    result = TOOL_FUNCTIONS["papers"](query="retrieval augmented generation", max_results=2)
    assert calls[0]["params"]["max_results"] == 2
    assert calls[0]["params"]["search_query"] == "all:retrieval AND all:augmented AND all:generation"
    assert result["total_results"] == 1
    assert result["items"][0]["arxiv_id"] == "2303.08774"
    assert result["items"][0]["authors"] == ["Example Author"]
    assert result["items"][0]["summary"] == "Evidence summary"


def test_paper_text_saves_bounded_excerpt_in_temp_directory(monkeypatch, tmp_path) -> None:
    from tools.paper_text import tool as paper_module

    pdf_path = tmp_path / "2303.08774.pdf"
    monkeypatch.setattr(paper_module, "_download_arxiv_pdf", lambda _: (
        "2303.08774", pdf_path, "https://arxiv.org/pdf/2303.08774.pdf",
    ))
    observed_pages = []

    def extract(path, max_pages):
        assert path == pdf_path
        observed_pages.append(max_pages)
        return "x" * 2500, 12

    monkeypatch.setattr(paper_module, "_extract_pdf_text", extract)
    result = TOOL_FUNCTIONS["paper_text"](arxiv_url="2303.08774", max_pages=2, max_chars=1200)
    assert observed_pages == [2]
    assert result["pages_read"] == 2
    assert result["page_count"] == 12
    assert result["chars_returned"] == 1200
    assert result["items"][0]["summary"] == "x" * 1200
    assert pdf_path.with_suffix(".txt").read_text() == "x" * 1200
