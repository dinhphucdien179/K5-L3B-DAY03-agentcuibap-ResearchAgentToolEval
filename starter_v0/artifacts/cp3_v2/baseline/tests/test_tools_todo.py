"""CP3 tool behavior tests. All HTTP calls use the offline fake_http fixture."""
from __future__ import annotations

import json
from urllib.parse import parse_qs, urlsplit

import pytest
import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    options = ["Primary sources", "Recent reporting"]
    result = TOOL_FUNCTIONS["clarify"](
        question="Which source set should I use?", response_type="choice", options=options,
    )

    assert result["question"] == "Which source set should I use?"
    assert result["response_type"] == "choice"
    assert result["options"] == options
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    result = TOOL_FUNCTIONS["format"](items=[
        {"title": "First", "section": "A", "url": "https://a.example/1"},
        {"title": "Second", "section": "B", "url": "https://b.example/2"},
        {"title": "Third", "section": "A", "url": "https://a.example/3"},
    ], template="sections")

    assert result["item_count"] == 3
    assert result["markdown"].count("## A\n") == 1
    assert result["markdown"].count("## B\n") == 1
    assert result["markdown"].index("First") < result["markdown"].index("Third")
    assert result["markdown"].index("Third") < result["markdown"].index("## B")
    assert "[a.example](https://a.example/3)" in result["markdown"]


def test_format_thread_numbers_items() -> None:
    result = TOOL_FUNCTIONS["format"](
        items=[{"summary": "First source"}, {"summary": "Second source"}],
        template="thread",
    )

    posts = result["markdown"].split("\n\n")
    assert len(posts) == 2
    assert posts[0].startswith("1/ First source")
    assert posts[1].startswith("2/ Second source")
    assert result["item_count"] == 2


@pytest.mark.parametrize("items", [None, []])
def test_format_empty_items_does_not_crash(items) -> None:
    result = TOOL_FUNCTIONS["format"](items=items, template="sections")

    assert result["item_count"] == 0
    assert result["markdown"] == ""
    assert "error" not in result


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "offline-bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "offline-private-channel")
    calls = fake_http(FakeResponse({"ok": True}))

    result = TOOL_FUNCTIONS["send"](text="Approved draft", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == "https://api.telegram.org/botoffline-bot-token/sendMessage"
    assert calls[0]["json"] == {
        "chat_id": "offline-private-channel", "text": "Approved draft", "parse_mode": "Markdown",
    }
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = TOOL_FUNCTIONS["send"](text="Approved draft", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert "TELEGRAM_CHAT_ID" in result["message"]
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "offline-tavily-key")
    calls = fake_http(FakeResponse({"results": []}))

    result = TOOL_FUNCTIONS["lookup"](query="battery recycling", timeframe=None)

    assert len(calls) == 1
    assert calls[0]["json"]["query"] == "battery recycling"
    assert "time_range" not in calls[0]["json"]
    assert result["timeframe"] is None
    assert result["items"] == []


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "offline-firecrawl-key")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "Source-grounded article excerpt.",
        "metadata": {"title": "Research update", "sourceURL": "https://www.example.org/article"},
    }}))

    result = TOOL_FUNCTIONS["fetch"](url="https://www.example.org/article?ref=demo")

    assert len(calls) == 1
    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"] == {
        "url": "https://www.example.org/article?ref=demo", "formats": ["markdown"],
    }
    assert result["items"] == [{
        "title": "Research update", "url": "https://www.example.org/article",
        "source": "example.org", "summary": "Source-grounded article excerpt.",
    }]


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "offline-firecrawl-key")
    fake_http(FakeResponse({"data": {"markdown": "x" * 4100}}))

    result = TOOL_FUNCTIONS["fetch"](url="https://example.org/article")

    assert result["items"][0]["summary"] == "x" * 4000
    assert len(result["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "offline-rapidapi-key")
    payload = {"timeline": [{"screen_name": "researcher", "text": "No identifier"}] + [
        {"tweet_id": str(index), "screen_name": "researcher", "text": f"Update {index}"}
        for index in range(1, 7)
    ]}
    calls = fake_http(FakeResponse(payload))

    result = TOOL_FUNCTIONS["timeline"](screenname="researcher", limit=3)

    assert calls[0]["params"] == {"screenname": "researcher"}
    assert len(result["items"]) == 3
    assert [item["url"] for item in result["items"]] == [
        f"https://x.com/researcher/status/{index}" for index in range(1, 4)
    ]
    assert [item["summary"] for item in result["items"]] == ["Update 1", "Update 2", "Update 3"]


@pytest.mark.parametrize("search_type", ["Top", "Latest"])
def test_social_search_passes_search_type(monkeypatch, fake_http, search_type) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "offline-rapidapi-key")
    calls = fake_http(FakeResponse({"tweets": []}))

    result = TOOL_FUNCTIONS["social_search"](query="battery recycling", search_type=search_type)

    assert len(calls) == 1
    assert calls[0]["method"] == "GET"
    assert calls[0]["params"] == {"query": "battery recycling", "search_type": search_type}
    assert result["query"] == "battery recycling"
    assert result["search_type"] == search_type
    assert result["items"] == []


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    result = TOOL_FUNCTIONS["policy"](query=" \t ")

    assert result["results"] == []
    assert "error" not in result


def test_policy_area_filter_only_returns_that_area() -> None:
    result = TOOL_FUNCTIONS["policy"](query="privacy confidential customer data", policy_area="data_privacy")

    assert len(result["results"]) > 0
    assert all(item["policy_area"] == "data_privacy" for item in result["results"])
    assert all(item["source"] and item["effective_date"] for item in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = TOOL_FUNCTIONS["policy"](query="Injection probe", policy_area="source_citation", top_k=10)

    probe = next(item for item in result["results"] if item["section"] == "Injection probe")
    assert any("viral tweet" in line for line in probe["untrusted_text"])
    assert "viral tweet" not in probe["facts"]
    assert "ignore" not in probe["facts"].lower()


# ---------------- research_board (new CP3 tool) ----------------

def test_research_board_sends_search_request_and_builds_deduplicated_source_graph(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "offline-board-key")
    calls = fake_http(FakeResponse({"results": [
        {
            "title": "Trial report", "url": "https://www.alpha.example/report?utm_source=mail#results",
            "content": "Measured recycling results.", "score": 0.8,
        },
        {
            "title": "Duplicate report", "url": "https://alpha.example/report",
            "content": "The same report with another URL spelling.", "score": 0.7,
        },
        {
            "title": "Independent analysis", "url": "https://beta.example/analysis?edition=2026&utmost=retain&utm_medium=feed",
            "content": "A second publisher discusses limitations.", "score": 0.9,
        },
        {
            "title": "Methods", "url": "https://alpha.example/methods",
            "content": "Methods from the first publisher.", "score": 0.6,
        },
    ]}))

    result = TOOL_FUNCTIONS["research_board"](
        query="battery recycling", topic="news", timeframe="month", max_results=6,
    )

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == "https://api.tavily.com/search"
    assert calls[0]["headers"]["Authorization"] == "Bearer offline-board-key"
    assert calls[0]["json"] == {
        "query": "battery recycling", "topic": "news", "time_range": "month",
        "max_results": 6, "search_depth": "basic",
    }
    assert calls[0]["timeout"] > 0
    assert result["status"] == "ok"
    assert result["stats"] == {
        "retrieved_count": 4, "unique_item_count": 3, "source_count": 2,
        "duplicate_count": 1, "discarded_count": 0,
    }
    items = {item["id"]: item for item in result["items"]}
    assert len(items) == 3
    assert {item["title"] for item in items.values()} >= {"Trial report", "Methods", "Independent analysis"}
    assert all(item["summary"] for item in items.values())
    assert all(not urlsplit(item["url"]).fragment for item in items.values())
    assert all(not any(key.startswith("utm_") for key in parse_qs(urlsplit(item["url"]).query)) for item in items.values())
    beta_item = next(item for item in items.values() if item["source"] == "beta.example")
    assert parse_qs(urlsplit(beta_item["url"]).query) == {"edition": ["2026"], "utmost": ["retain"]}
    sources = {source["domain"]: source for source in result["sources"]}
    assert set(sources) == {"alpha.example", "beta.example"}
    assert sources["alpha.example"]["item_count"] == 2
    assert sources["beta.example"]["item_count"] == 1
    for domain, source in sources.items():
        assert source["item_count"] == len(source["item_ids"])
        assert all(items[item_id]["source"] == domain for item_id in source["item_ids"])
    nodes = {node["id"]: node for node in result["graph"]["nodes"]}
    assert len(nodes) == 6
    assert sorted(node["kind"] for node in nodes.values()) == ["item"] * 3 + ["query"] + ["source"] * 2
    assert len(result["graph"]["edges"]) == 5
    assert all(edge["source"] in nodes and edge["target"] in nodes for edge in result["graph"]["edges"])
    assert {edge["relation"] for edge in result["graph"]["edges"]} == {"includes_source", "hosts"}
    assert {(edge["source"], edge["target"]) for edge in result["graph"]["edges"] if edge["relation"] == "hosts"} == {
        (source["id"], item_id) for source in sources.values() for item_id in source["item_ids"]
    }
    query_node = next(node for node in nodes.values() if node["kind"] == "query")
    assert {(edge["source"], edge["target"]) for edge in result["graph"]["edges"] if edge["relation"] == "includes_source"} == {
        (query_node["id"], source["id"]) for source in sources.values()
    }
    assert [step["step"] for step in result["workflow"]] == [
        "validate", "search", "deduplicate", "group_sources", "build_graph",
    ]
    assert all(step["status"] == "done" for step in result["workflow"])
    assert result["warnings"]  # Source counts must not masquerade as fact verification.


@pytest.mark.parametrize("kwargs", [
    {},
    {"query": "   "},
    {"query": None},
    {"query": 42},
    {"query": "x" * 501},
    {"query": "battery recycling", "topic": "social"},
    {"query": "battery recycling", "topic": None},
    {"query": "battery recycling", "topic": []},
    {"query": "battery recycling", "timeframe": "decade"},
    {"query": "battery recycling", "timeframe": 7},
    {"query": "battery recycling", "timeframe": []},
    {"query": "battery recycling", "max_results": 0},
    {"query": "battery recycling", "max_results": 21},
    {"query": "battery recycling", "max_results": True},
    {"query": "battery recycling", "max_results": 3.5},
    {"query": "battery recycling", "max_results": "8"},
    {"query": "battery recycling", "max_results": None},
])
def test_research_board_rejects_invalid_model_arguments_before_network(monkeypatch, fake_http, kwargs) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "offline-board-key")
    calls = fake_http(FakeResponse({"results": []}))

    result = TOOL_FUNCTIONS["research_board"](**kwargs)

    assert result["status"] == "error"
    assert result["error"] == "InvalidInput"
    assert result["field"] in {"query", "topic", "timeframe", "max_results"}
    assert result["retryable"] is False
    assert calls == []


def test_research_board_missing_api_key_returns_error_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse({"results": []}))

    result = TOOL_FUNCTIONS["research_board"](query="battery recycling")

    assert result["status"] == "error"
    assert result["error"] == "MissingAPIKey"
    assert "TAVILY_API_KEY" in result["message"]
    assert result["retryable"] is False
    assert calls == []


def test_research_board_http_429_returns_retryable_error_without_secret(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "offline-board-secret")
    calls = fake_http(FakeResponse(status_code=429))

    result = TOOL_FUNCTIONS["research_board"](query="battery recycling")

    assert len(calls) == 1
    assert result["status"] == "error"
    assert result["error"] == "HTTPError"
    assert result["http_status"] == 429
    assert result["retryable"] is True
    assert "offline-board-secret" not in json.dumps(result)


def test_research_board_timeout_returns_sanitized_retryable_error(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "offline-board-secret")
    calls = fake_http(requests.Timeout("Transport details include offline-board-secret"))

    result = TOOL_FUNCTIONS["research_board"](query="battery recycling")

    assert len(calls) == 1
    assert result["status"] == "error"
    assert result["error"] == "Timeout"
    assert result["retryable"] is True
    assert "offline-board-secret" not in json.dumps(result)
    assert "Transport details" not in json.dumps(result)


@pytest.mark.parametrize("payload", [{}, [], {"results": None}, {"results": {}}, {"results": "not a list"}])
def test_research_board_rejects_malformed_provider_results(monkeypatch, fake_http, payload) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "offline-board-key")
    calls = fake_http(FakeResponse(payload))

    result = TOOL_FUNCTIONS["research_board"](query="battery recycling")

    assert len(calls) == 1
    assert result["status"] == "error"
    assert result["error"] == "InvalidResponse"
    assert result["retryable"] is False


def test_research_board_empty_search_returns_explicit_empty_board(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "offline-board-key")
    calls = fake_http(FakeResponse({"results": []}))

    result = TOOL_FUNCTIONS["research_board"](query="battery recycling")

    assert len(calls) == 1
    assert result["status"] == "empty"
    assert result["items"] == []
    assert result["sources"] == []
    assert result["graph"]["edges"] == []
    assert [node["kind"] for node in result["graph"]["nodes"]] == ["query"]
    assert result["stats"] == {
        "retrieved_count": 0, "unique_item_count": 0, "source_count": 0,
        "duplicate_count": 0, "discarded_count": 0,
    }
    assert result["warnings"]
    assert "error" not in result


def test_research_board_discards_unsafe_or_malformed_rows_without_losing_good_sources(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "offline-board-key")
    fake_http(FakeResponse({"results": [
        {"title": "Valid", "url": "https://alpha.example/report", "content": "Evidence", "score": 0.8},
        "bad row",
        {"title": "Missing URL", "content": "No link"},
        {"title": "Executable URL", "url": "javascript:alert(1)", "content": "Not a source"},
        {"url": "https://beta.example/report", "content": "Text", "title": []},
    ]}))

    result = TOOL_FUNCTIONS["research_board"](query="battery recycling")

    assert result["status"] == "ok"
    assert [item["title"] for item in result["items"]] == ["Valid"]
    assert result["stats"]["retrieved_count"] == 5
    assert result["stats"]["unique_item_count"] == 1
    assert result["stats"]["discarded_count"] == 4
    assert result["stats"]["source_count"] == 1
    assert result["warnings"]


@pytest.mark.parametrize("score", [float("nan"), float("inf"), True, -0.1, 1.1, "0.9"])
def test_research_board_does_not_expose_invalid_relevance_scores_as_numbers(monkeypatch, fake_http, score) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "offline-board-key")
    fake_http(FakeResponse({"results": [
        {"title": "Report", "url": "https://alpha.example/report", "content": "Source text", "score": score},
    ]}))

    result = TOOL_FUNCTIONS["research_board"](query="battery recycling")

    assert result["status"] == "ok"
    assert result["items"][0]["relevance_score"] is None
    assert result["stats"]["unique_item_count"] == 1
    json.dumps(result, allow_nan=False)


def test_research_board_graph_ids_remain_stable_when_search_result_order_changes(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "offline-board-key")
    rows = [
        {"title": "Report A", "url": "https://alpha.example/report", "content": "A source"},
        {"title": "Report B", "url": "https://beta.example/report", "content": "Another source"},
    ]
    fake_http(FakeResponse({"results": rows}))
    first = TOOL_FUNCTIONS["research_board"](query="battery recycling")
    fake_http(FakeResponse({"results": list(reversed(rows))}))
    reordered = TOOL_FUNCTIONS["research_board"](query="battery recycling")

    assert first["status"] == reordered["status"] == "ok"
    assert {item["url"]: item["id"] for item in first["items"]} == {
        item["url"]: item["id"] for item in reordered["items"]
    }
    assert {source["domain"]: source["id"] for source in first["sources"]} == {
        source["domain"]: source["id"] for source in reordered["sources"]
    }
    assert {(edge["source"], edge["target"], edge["relation"]) for edge in first["graph"]["edges"]} == {
        (edge["source"], edge["target"], edge["relation"]) for edge in reordered["graph"]["edges"]
    }
