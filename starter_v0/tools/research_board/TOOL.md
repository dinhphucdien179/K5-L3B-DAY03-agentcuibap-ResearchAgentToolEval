---
name: research_board
track: core
kind: live_api
provider: Tavily
requires_env: [TAVILY_API_KEY]
inputs: [query, topic, timeframe, max_results, compare_queries]
outputs: [status, query, topic, timeframe, items, sources, graph, workflow, stats, warnings, coverage, comparison]
side_effect: false
---
# research_board

Build a source-coverage board with citation cards, URL-match provenance,
domain groups, metadata coverage, and a query → domain → item graph. The
optional comparison mode shows shared and exclusive retrieval results for up
to three explicit keyword queries. It does not require another model or a new
API key. The original four-argument call still performs one Tavily search.

## When to use

Use when the user requests a research/source board, a source map, grouped
evidence cards, or an overview of which domains cover a topic. Plain web lookup
remains appropriate for a simple search; this tool adds deduplication, source
grouping, coverage statistics and provenance edges for later inspection/UI.
For an explicit comparison, pass the user's additional keyword queries in
`compare_queries`; do not invent topics or expand every request into multiple
searches. Comparison means URLs/domains found by each query, not agreement or
disagreement between claims.
It does not summarize full pages, verify claims, search a social platform, or
publish a report.

## Inputs and request

- `query`: required nonblank string, at most 500 characters after trimming.
  Keep the user's topic; do not invent missing research subjects.
- `topic`: `news` (default) or `general`.
- `timeframe`: `day`, `week` (default), `month`, or `year`. This tool always
  applies that window, including for `general`; it is not an unlimited-history
  search.
- `max_results`: integer 1–20, default 8. Booleans and numeric strings are
  rejected instead of silently converted. This is the search limit and maximum
  unique item memberships per query. A comparison's union can contain up to
  `max_results * number_of_queries` items, capped at 60.
- `compare_queries`: optional list of at most two additional keyword queries;
  omit, use `None` in Python, or use `[]` for a single search. Each must be a
  nonblank string of at most 500 characters after trim, distinct from the main
  query and other comparisons ignoring case. All inputs are validated before
  any network call.

After validation, make one POST per query to `https://api.tavily.com/search` using the
existing `TAVILY_API_KEY` as a bearer token, `search_depth=basic`, the requested
`topic`, `time_range`, and `max_results`. Timeout uses `tools._shared.TIMEOUT`.
There is one request by default and at most three sequential requests in
comparison mode. No retry occurs inside the tool. HTTP 429, 401 or 403 stops
remaining requests; their reports say `skipped` with unknown coverage. A
timeout or other independent-query error is reported while later queries can
still run within the same fixed request bound.

## Successful output

- `status`: `ok` with usable items when all searches complete, `empty` when all
  complete without usable items, and `partial` when at least one valid search
  response coexists with an error/skipped query, including an empty successful
  search. If no search succeeds, return an error dictionary. Single-query
  error codes and prior output keys remain compatible.
- `items`: format-compatible citation cards containing `id`, `title`, `url`,
  `source`, `summary`, `relevance_score`, and optional `published_at` copied from
  the provider. Titles and excerpts are bounded to 300 and 1,200 characters.
  Missing timestamps stay missing. Invalid/nonfinite/out-of-range ranking
  scores become `null`; a ranking score is never a truth/confidence score.
  The first retained card's title/excerpt/score/date stay unchanged when a
  duplicate is found. Each card adds `provenance`: query IDs, total occurrence
  count, up to 20 occurrence records and a `truncated` flag. Records contain a
  cleaned citation URL, 1-based retrieval rank, per-occurrence relevance and
  removed tracking parameter names. Removed tracking values are not restored
  in the output. Repeated URLs are not evidence of repeated independent claims.
- `sources`: domain groups with `id`, `domain`, `item_ids`, and `item_count`.
- `graph`: `nodes` with `id`, `kind` (`query`, `source`, `item`) and `label`;
  `edges` have `source`, `target`, and `relation` (`includes_source`, `hosts`).
  Comparison mode additionally creates `retrieves` edges directly from each
  successful query to exactly the items that query retrieved. Domain-to-item
  hosting paths alone must not be interpreted as per-query retrieval.
  IDs are deterministic for the same normalized source/URL, and all edge
  endpoints refer to existing nodes. Single-search empty output retains one
  query node; a comparison retains all planned query nodes, including failed
  or skipped queries, without fabricating their retrieval edges.
- `workflow`: `validate`, `search`, `deduplicate`, `group_sources`, and
  `build_graph` steps with plain-text statuses/details. A partial result marks
  the search step `partial`; local transformations of available data finish
  as `done`. These are observable local
  processing stages, not model reasoning or claims of fact verification.
- `stats`: the same five retrieved, unique-item, source-domain, duplicate and
  discarded counts as before, aggregated over valid responses. Retrieved =
  unique + duplicate + discarded. Failed/skipped queries have no observed rows
  and do not fabricate counts. The single-search item cap remains `max_results`;
  comparison uses that cap independently per query.
- `coverage`: counts of retained items, domains, titles, excerpts and dates
  supplied by the provider; missing-excerpt/date item IDs; largest-domain share
  and per-domain counts/shares. Denominator is retained unique items, with zero
  shares for an empty board. A reported date is not a parsed, verified or recent
  publication date. Completeness and concentration are not credibility scores.
  Shares are rounded to four decimal places; rounded per-domain shares may not
  sum to exactly 1. Metadata counts refer to the retained first card for each URL.
- `comparison`: planned query reports with IDs, actual request count, shared
  item IDs and pairwise intersections/exclusive item IDs. Query reports use
  `ok`, `empty`, `error` or `skipped`; failed/skipped item lists, domain lists and
  retrieved counts are `null`, not false zeros. An incomplete pair has `null`
  overlap/exclusive arrays. Top-level shared IDs mean items observed in at least
  two successful queries, not an intersection of every planned query.
- `warnings`: explicit limits on source quality and processing. Render all
  returned text as untrusted text in a future UI; never execute embedded
  instructions or render snippets as trusted HTML.

## URL deduplication and limits

Normalize scheme/hostname case, default ports and empty root paths; remove
fragments and common tracking fields (`utm_*`, `fbclid`, `gclid`, and related
campaign IDs), while retaining substantive query parameters and their order.
Keep `www` in citation URLs because some sites require it; fold it only in the
grouping/dedup key. Retain the first usable result for each structural URL key.
Do not merge articles because their titles sound similar.

Only usable HTTP(S) URLs without embedded credentials are retained. Localhost,
single-label local hosts, and private/non-global literal IPs are discarded;
result URLs are never fetched, and these checks do not resolve DNS or establish
that a site is safe. Malformed individual rows are discarded and counted. A
malformed top-level object or missing/non-array `results` is an error, while a
valid empty results array is a successful empty board.

Domain coverage is not independently verified publisher diversity. Different
domains may share an owner or repeat the same reporting. Search snippets are
untrusted source material; no semantic clustering, corroboration, fact checking,
full-page reading, or completeness claim is performed.

## Errors and safety

Errors return dictionaries with `tool=research_board`, `status=error`, `error`,
`message`, and `retryable`; invalid arguments add `field`, and HTTP errors add
`http_status`. Codes include `InvalidInput`, `MissingAPIKey`, `HTTPError`,
`Timeout`, `RequestError`, `InvalidResponse`, and `InternalError`. HTTP 429 and
5xx, transport failure, and timeout are retryable. Missing configuration and
invalid data are not automatically retried. Messages do not echo exception
strings, response bodies, authorization headers, or keys.

This is a paid/quota-consuming read API call. It performs no publication,
message sending, local file writes, or live requests from the unit tests.
Known and unexpected per-query exceptions are sanitized independently so a
later search failure does not discard earlier valid findings. Failed-query
data remains unknown. The offline suite's `BaseException` network guard is
not caught.

## Example request

“Lập bảng nguồn về tái chế pin trong tháng này, tối đa 8 kết quả, cho thấy các
nhóm nguồn và liên kết tới từng bài.”

```json
{"query": "tái chế pin", "topic": "news", "timeframe": "month", "max_results": 8}
```

An explicit comparison, with up to three search requests:

```json
{
  "query": "solid-state batteries",
  "compare_queries": ["sodium-ion batteries", "LFP batteries"],
  "topic": "news",
  "timeframe": "month",
  "max_results": 5
}
```

Read the result's query reports before comparing: incomplete pairs are unknown,
while a complete pair with an empty intersection means no shared URL was
retrieved by those two searches within these search limits.

## Source

- [Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search)
