"""Regression tests for resilient research evidence and source identity."""
from __future__ import annotations

import pytest

from tools.citation_audit.tool import audit_citations
from tools.deduplicate.tool import deduplicate_sources, source_url_key
from tools.investigate.tool import investigate_topic


@pytest.mark.parametrize("bad_result", [None, [], "upstream unavailable", {"items": None}])
def test_investigate_keeps_evidence_when_another_search_has_malformed_payload(monkeypatch, bad_result):
    responses = iter([
        {"items": [{"url": "https://example.org/benefits", "summary": "Measured benefit"}]},
        bad_result,
    ])
    monkeypatch.setattr("tools.investigate.tool.web_search", lambda **kwargs: next(responses))

    result = investigate_topic("RAG", ["benefits", "limitations"], sources_per_angle=1)

    assert result["status"] == "partial"
    assert result["source_count"] == 1
    assert result["sources"][0]["excerpts"][0]["text"] == "Measured benefit"
    assert result["sections"][0]["source_ids"] == ["S1"]
    assert result["sections"][1]["source_ids"] == []
    assert result["gaps"][0]["angle"] == "limitations"


def test_investigate_isolates_unexpected_search_exception_without_retrying(monkeypatch):
    queries = []

    def search(**kwargs):
        queries.append(kwargs["query"])
        if len(queries) == 1:
            raise RuntimeError("unexpected response decoding failure")
        return {"items": [{"url": "https://example.org/limits", "summary": "Measured limitation"}]}

    monkeypatch.setattr("tools.investigate.tool.web_search", search)
    result = investigate_topic("RAG", ["benefits", "limitations"], sources_per_angle=1)

    assert len(queries) == 2
    assert result["status"] == "partial"
    assert result["source_count"] == 1
    assert result["search_errors"][0]["angle"] == "benefits"
    assert result["search_errors"][0]["error"] == "RuntimeError"


def test_investigate_counts_hostnames_case_insensitively_and_normalizes_title(monkeypatch):
    responses = iter([
        {"items": [{"url": "https://EXAMPLE.org/one", "summary": "One", "title": {"wrong": "shape"}}]},
        {"items": [{"url": "https://example.org/two", "summary": "Two"}]},
    ])
    monkeypatch.setattr("tools.investigate.tool.web_search", lambda **kwargs: next(responses))

    result = investigate_topic("RAG", ["benefits", "limitations"], sources_per_angle=1)

    assert result["source_count"] == 2
    assert result["domain_count"] == 1
    assert all(source["title"] == "Untitled" for source in result["sources"])


@pytest.mark.parametrize("url", [
    "https://bad host.example/doc", "https://exa\nmple.org/doc",
    "https://example.org/a\tb", "https://example.org/\x00doc",
])
def test_malformed_whitespace_url_cannot_become_deduplicated_or_resolved_source(url):
    assert "error" in deduplicate_sources([{"url": url}])
    result = audit_citations("A finding. [S1]", [{"id": "S1", "url": url}])
    assert result["resolved_source_ids"] == []
    assert result["unresolved_citations"][0]["reason"] == "invalid_source_url"


def test_source_url_identity_preserves_case_sensitive_credentials():
    assert source_url_key("https://Alice:Secret@EXAMPLE.org/doc") != source_url_key(
        "https://alice:secret@example.org/doc")
    assert source_url_key("https://Alice:Secret@EXAMPLE.org/doc") == source_url_key(
        "https://Alice:Secret@example.org/doc#section")


def test_audit_escaped_brackets_do_not_count_literal_examples_as_citations():
    result = audit_citations(r"A literal example \[S1] is not a reference.", [
        {"id": "S1", "url": "https://example.org/doc"},
    ])
    assert result["citation_count"] == 0
    assert result["coverage"]["cited_blocks"] == 0
    assert result["unused_source_ids"] == ["S1"]


def test_audit_even_backslashes_leave_the_following_citation_active():
    result = audit_citations(r"Two slashes \\[S1] leave a real reference.", [
        {"id": "S1", "url": "https://example.org/doc"},
    ])
    assert result["citation_count"] == 1
    assert result["resolved_source_ids"] == ["S1"]


def test_audit_fence_with_trailing_text_does_not_end_code_block():
    result = audit_citations(
        "```text\n```still code\nA code example [S99]\n```\n\nA real finding. [S1]",
        [{"id": "S1", "url": "https://example.org/doc"}],
    )
    assert result["cited_source_ids"] == ["S1"]
    assert result["unresolved_citations"] == []
    assert result["coverage"] == {"total_blocks": 1, "cited_blocks": 1, "ratio": 1.0}
