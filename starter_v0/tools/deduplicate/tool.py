"""Remove duplicate research sources by URL without changing their content."""
from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def source_url_key(url: str) -> str:
    """Canonical comparison key; raise ValueError for unsupported/malformed URLs."""
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("must be an absolute HTTP(S) URL")
    parts.port
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/",
                       urlencode(sorted(query)), ""))


def deduplicate_sources(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep the first source for each URL; ignore fragments and tracking params."""
    if not isinstance(items, list):
        return {"error": "items must be a list of objects with HTTP(S) URLs"}
    unique = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("url"), str):
            return {"error": f"items[{index}] must have a string url"}
        try:
            url = item["url"].strip()
            parts = urlsplit(url)
            if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
                return {"error": f"items[{index}].url must be an absolute HTTP(S) URL"}
            key = source_url_key(url)
        except ValueError:
            return {"error": f"items[{index}].url is malformed"}
        if key not in seen:
            seen.add(key)
            unique.append(dict(item))
    return {"items": unique, "item_count": len(unique), "removed_count": len(items) - len(unique)}
