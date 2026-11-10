"""Offline behavior tests for the comparison and citation workbench tools."""
from __future__ import annotations

from copy import deepcopy

import pytest
import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS
from tools.citation_audit.tool import audit_citations
from tools.compare_research.tool import compare_research








def test_comparison_http_failure_preserves_successful_cells(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs["json"])
        if len(calls) == 1:
            raise requests.Timeout("search timed out")
        return FakeResponse({"results": [
            {"url": "https://docs.example.org/b", "content": "Useful measured evidence"},
        ]})

    monkeypatch.setattr(requests, "post", fake_post)
    result = compare_research(["A", "B"], ["latency"], timeframe="month", sources_per_cell=1)
    assert result["status"] == "partial"
    assert result["covered_cells"] == 1
    assert result["gaps"] == [{"subject": "A", "criterion": "latency", "reason": "search_failed"}]
    assert result["cells"][1]["evidence"][0]["source_id"] == "S1"
    assert all(call["time_range"] == "month" and call["max_results"] == 1 for call in calls)


def test_comparison_malformed_sources_are_reported_as_gaps(monkeypatch, fake_http):
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    fake_http(FakeResponse({"results": [
        {"url": "https://[broken", "content": "Bad URL"},
        {"url": "https://example.org/empty", "content": " "},
        {"url": "ftp://example.org/file", "content": "Unsupported URL"},
    ]}))
    result = compare_research(["A", "B"], ["cost"], sources_per_cell=3)
    assert result["status"] == "error"
    assert all(cell["skipped_results"] == 3 for cell in result["cells"])
    assert all(gap["reason"] == "no_usable_sources" for gap in result["gaps"])


def test_comparison_handles_non_list_search_payload(monkeypatch):
    monkeypatch.setattr("tools.compare_research.tool.web_search", lambda **kwargs: {"items": None})
    result = compare_research(["A", "B"], ["cost"])
    assert result["status"] == "error"
    assert len(result["gaps"]) == 2


def test_comparison_preserves_distinct_cell_excerpts_from_one_shared_source(monkeypatch):
    def search(**kwargs):
        return {"items": [{"url": "https://example.org/shared", "summary": kwargs["query"]}]}

    monkeypatch.setattr("tools.compare_research.tool.web_search", search)
    result = compare_research(["Product A", "Product B"], ["latency", "cost"])
    assert result["source_count"] == 1
    assert len({cell["evidence"][0]["excerpt"] for cell in result["cells"]}) == 4
    assert all(cell["evidence"][0]["excerpt"] == cell["query"] for cell in result["cells"])


def test_comparison_maximum_matrix_is_bounded_to_nine_requests(monkeypatch, fake_http):
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    calls = fake_http(FakeResponse({"results": [{"url": "https://example.org/docs", "content": "Evidence"}]}))
    result = compare_research(["A", "B", "C"], ["latency", "cost", "availability"])
    assert len(calls) == result["total_cells"] == 9
    assert result["status"] == "complete"








def test_audit_duplicate_ids_and_invalid_urls_cannot_resolve_references():
    result = audit_citations("This paragraph cites catalog problems. [S1; S2]", [
        {"id": "S1", "url": "https://example.org/one"},
        {"id": "S1", "url": "https://example.org/two"},
        {"id": "S2", "url": "https://[broken"},
    ])
    assert result["resolved_source_ids"] == []
    assert {item["reason"] for item in result["unresolved_citations"]} == {
        "ambiguous_source_id", "invalid_source_url",
    }
    assert {item["type"] for item in result["catalog_issues"]} == {"duplicate_id", "invalid_url"}


def test_audit_duplicate_urls_are_detected_after_tracking_removal():
    result = audit_citations("Two aliases point to one source. [S1, S2]", [
        {"id": "S1", "url": "https://example.org/doc?utm_campaign=one#header"},
        {"id": "S2", "url": "https://example.org/doc"},
    ])
    assert result["catalog_issues"] == [{"type": "duplicate_url", "source_ids": ["S1", "S2"]}]
    assert result["status"] == "review_needed"
    assert result["coverage"]["cited_blocks"] == 1


def test_audit_ignores_code_examples_and_preserves_real_line_numbers():
    result = audit_citations(
        "# Example\n\n```markdown\nFake reference [S9]\n```\n\n"
        "Inline `fake [S8]` is ignored, real reference stays. [S1]\n\nAnother claim. [S7]",
        [{"id": "S1", "url": "https://example.org/one"}],
    )
    assert result["cited_source_ids"] == ["S1", "S7"]
    assert result["unresolved_citations"] == [{"source_id": "S7", "reason": "unknown_source_id", "lines": [9]}]
    assert result["coverage"] == {"total_blocks": 2, "cited_blocks": 1, "ratio": 0.5}


def test_audit_heading_only_draft_has_undefined_coverage_not_false_success_percentage():
    result = audit_citations("# Research notes", [])
    assert result["coverage"] == {"total_blocks": 0, "cited_blocks": 0, "ratio": None}


def test_audit_missing_catalog_url_is_a_reported_issue_not_a_crash():
    result = audit_citations("A claim with a missing URL. [S1]", [{"id": "S1"}])
    assert result["catalog_issues"] == [{"type": "invalid_url", "source_id": "S1", "index": 0}]
    assert result["unresolved_citations"][0]["reason"] == "invalid_source_url"


def test_audit_markdown_links_resolve_against_catalog_without_fetching_url(fake_http):
    calls = fake_http(FakeResponse())
    result = audit_citations("Read this cited finding. [S1](https://example.org/linked)", [
        {"id": "S1", "url": "https://example.org/catalog"},
    ])
    assert result["resolved_source_ids"] == ["S1"]
    assert calls == []


def test_workbench_tools_are_registered():
    assert TOOL_FUNCTIONS["compare_research"] is compare_research
    assert TOOL_FUNCTIONS["citation_audit"] is audit_citations
