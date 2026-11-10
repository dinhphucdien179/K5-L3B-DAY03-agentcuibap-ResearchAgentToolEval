"""Audit explicit source references in a draft without judging factual truth."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

from tools.deduplicate.tool import source_url_key

SOURCE_ID = re.compile(r"S[1-9][0-9]{0,5}\Z")
# Accept [S1], [S1, S2], [S1; S2], including Markdown [S1](url).
CITATION_GROUP = re.compile(r"\[(S[0-9]+(?:\s*[,;]\s*S[0-9]+)*)\]")


def _mask_code(text: str) -> str:
    """Preserve line numbers while ignoring fenced/inline code examples."""
    lines = text.splitlines(keepends=True)
    masked = []
    fence_char = ""
    fence_size = 0
    for line in lines:
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence_char:
            masked.append("".join("\n" if char == "\n" else " " for char in line))
            if (match and match[1][0] == fence_char and len(match[1]) >= fence_size
                    and not line[match.end():].strip()):
                fence_char = ""
            continue
        if match:
            fence_char, fence_size = match[1][0], len(match[1])
            masked.append("".join("\n" if char == "\n" else " " for char in line))
            continue
        line = re.sub(r"(`+)([^`\n]*?)\1", lambda m: " " * len(m[0]), line)
        # An odd run of backslashes escapes the bracket; an even run leaves a
        # real citation. Mask the escape sequence, preserving offsets.
        line = re.sub(r"(?<!\\)(?:\\\\)*\\\[", lambda m: " " * len(m[0]), line)
        masked.append(line)
    return "".join(masked)


def audit_citations(draft: str = "", sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Report citation coverage, unresolved IDs and malformed source catalogs."""
    if not isinstance(draft, str) or not draft.strip() or len(draft) > 50000:
        return {"error": "draft must be a non-empty string of at most 50000 characters"}
    if not isinstance(sources, list) or len(sources) > 100:
        return {"error": "sources must be a list of at most 100 source objects with id and url"}
    for index, source in enumerate(sources):
        if (not isinstance(source, dict) or not isinstance(source.get("id"), str)
                or not SOURCE_ID.fullmatch(source["id"])):
            return {"error": f"sources[{index}].id must use the format S1, S2, ... (up to six digits)"}

    counts = Counter(source["id"] for source in sources)
    catalog: dict[str, dict[str, Any]] = {}
    url_ids: dict[str, list[str]] = {}
    issues: list[dict[str, Any]] = []
    for index, source in enumerate(sources):
        source_id = source["id"]
        if source_id not in catalog:
            catalog[source_id] = {"id": source_id, "url": source.get("url"), "valid_url": False}
        try:
            if not isinstance(source.get("url"), str):
                raise ValueError("missing URL")
            key = source_url_key(source["url"])
        except ValueError:
            issues.append({"type": "invalid_url", "source_id": source_id, "index": index})
        else:
            catalog[source_id]["valid_url"] = True
            url_ids.setdefault(key, []).append(source_id)
    for source_id, count in counts.items():
        if count > 1:
            issues.append({"type": "duplicate_id", "source_id": source_id, "count": count})
    for source_ids in url_ids.values():
        unique_ids = list(dict.fromkeys(source_ids))
        if len(unique_ids) > 1:
            issues.append({"type": "duplicate_url", "source_ids": unique_ids})

    masked = _mask_code(draft)
    occurrences: dict[str, list[int]] = {}
    for match in CITATION_GROUP.finditer(masked):
        line = masked.count("\n", 0, match.start()) + 1
        for source_id in re.findall(r"S[0-9]+", match[1]):
            occurrences.setdefault(source_id, []).append(line)
    unresolved = []
    resolved_ids = []
    for source_id, lines in occurrences.items():
        reason = None
        if source_id not in catalog:
            reason = "unknown_source_id"
        elif counts[source_id] != 1:
            reason = "ambiguous_source_id"
        elif not catalog[source_id]["valid_url"]:
            reason = "invalid_source_url"
        if reason:
            unresolved.append({"source_id": source_id, "reason": reason, "lines": sorted(set(lines))})
        else:
            resolved_ids.append(source_id)

    blocks = []
    # A linear pass keeps line numbers exact, including blank lines and headings.
    paragraphs = []
    current_lines = []
    paragraph_line = 1
    for line_number, line in enumerate(masked.splitlines(), 1):
        if (not line.strip() or re.match(r"^\s{0,3}#{1,6}\s", line)
                or re.fullmatch(r"\s*[-=|: ]+\s*", line)):
            if current_lines:
                paragraphs.append((paragraph_line, "\n".join(current_lines).strip()))
                current_lines = []
            continue
        if not current_lines:
            paragraph_line = line_number
        current_lines.append(line)
    if current_lines:
        paragraphs.append((paragraph_line, "\n".join(current_lines).strip()))
    # Paragraph-level coverage is deliberately structural, not claim detection.
    for line_number, content in paragraphs:
        without_citations = CITATION_GROUP.sub("", content)
        if not re.search(r"[^\W_]{2,}", without_citations, re.UNICODE):
            continue
        ids = list(dict.fromkeys(source_id for citation in CITATION_GROUP.finditer(content)
                                 for source_id in re.findall(r"S[0-9]+", citation[1])))
        blocks.append({
            "block": len(blocks) + 1, "line": line_number,
            "text": content[:500], "citation_ids": ids,
            "has_resolved_citation": any(source_id in resolved_ids for source_id in ids),
        })
    uncited = [block for block in blocks if not block["has_resolved_citation"]]
    total = len(blocks)
    return {
        "tool": "citation_audit",
        "status": "review_needed" if issues or unresolved or uncited else "references_resolved",
        "source_count": len(sources), "citation_count": sum(len(lines) for lines in occurrences.values()),
        "cited_source_ids": list(occurrences), "resolved_source_ids": resolved_ids,
        "unresolved_citations": unresolved, "unused_source_ids": [source_id for source_id in catalog if source_id not in occurrences],
        "catalog_issues": issues, "blocks": blocks, "uncited_blocks": uncited,
        "coverage": {"total_blocks": total, "cited_blocks": total - len(uncited),
                     "ratio": round((total - len(uncited)) / total, 4) if total else None},
        "audit_note": (
            "Checks explicit [S1] or [S1, S2] references against a supplied source catalog. "
            "Fenced and inline code are ignored; coverage uses paragraphs, excluding Markdown headings. "
            "A cited paragraph may contain unsupported claims. Resolved references mean only that an ID "
            "has one catalog entry with a syntactically valid HTTP(S) URL; URLs are not visited. "
            "This is not factual verification or a verdict on source quality."
        ),
    }
