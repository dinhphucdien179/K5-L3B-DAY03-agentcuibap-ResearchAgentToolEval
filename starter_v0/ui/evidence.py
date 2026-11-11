from __future__ import annotations
from typing import Any
from urllib.parse import urlsplit
from ui.runtime import redact

def extract_sources(events: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Find cited source records in different tools' nested output formats."""
    sources: dict[str, dict[str, str]] = {}
    evidence_by_id: dict[str, str] = {}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            url = value.get("url") or value.get("source_url")
            if isinstance(url, str):
                try:
                    parsed = urlsplit(url)
                    valid = parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not parsed.username
                except ValueError:
                    valid = False
                if valid and url not in sources:
                    excerpt = value.get("summary") or value.get("abstract") or value.get("content") or ""
                    excerpts = value.get("excerpts")
                    if (not excerpt and isinstance(excerpts, list) and excerpts
                            and isinstance(excerpts[0], dict)):
                        excerpt = excerpts[0].get("text", "")
                    if not excerpt:
                        excerpt = evidence_by_id.get(str(value.get("id", "")), "")
                    sources[url] = {"url": url, "title": str(value.get("title") or parsed.hostname),
                                    "domain": parsed.hostname or "", "excerpt": str(excerpt)[:320],
                                    "id": str(value.get("id", ""))}
            for nested in value.values():
                if isinstance(nested, (dict, list)):
                    visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    for event in events:
        result = event.get("result", {})
        # Comparison tools keep snippets in matrix cells and URLs in a catalog.
        # Join within one event: S1 in another tool call may mean another source.
        evidence_by_id = {}
        if isinstance(result, dict):
            for cell in result.get("cells", []):
                if not isinstance(cell, dict):
                    continue
                for evidence in cell.get("evidence", []):
                    if isinstance(evidence, dict) and isinstance(evidence.get("excerpt"), str):
                        source_id = str(evidence.get("source_id", ""))
                        if source_id and source_id not in evidence_by_id:
                            evidence_by_id[source_id] = evidence["excerpt"]
        visit(result)
    return list(sources.values())

def tool_issues(events: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for event in events:
        result = event.get("result", {})
        if not isinstance(result, dict):
            continue
        name = event.get("tool", "tool")
        if result.get("error"):
            issues.append(f"{name}: {result['error']}" + (f" — {result['message']}" if result.get("message") else ""))
        elif result.get("status") == "partial" or result.get("search_errors"):
            coverage = (f" ({result['covered_cells']}/{result['total_cells']} ô có nguồn)"
                        if "covered_cells" in result and "total_cells" in result else "")
            issues.append(f"{name}: chỉ thu được một phần dữ liệu{coverage}. Xem các nguồn còn thiếu trong trace.")
        elif result.get("status") == "review_needed":
            issues.append(f"{name}: cần rà soát {len(result.get('unresolved_citations', []))} trích dẫn chưa khớp, "
                          f"{len(result.get('uncited_blocks', []))} đoạn thiếu trích dẫn hợp lệ và "
                          f"{len(result.get('catalog_issues', []))} lỗi danh mục nguồn. "
                          "Đây là kiểm tra cấu trúc tham chiếu, chưa xác minh tính đúng sai.")
    return redact(issues)
