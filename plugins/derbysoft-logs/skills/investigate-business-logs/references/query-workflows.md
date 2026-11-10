# Direct MCP query workflows

These are tool arguments to compose in memory, not instructions to create files or scripts. Select one environment and carry its explicit name through every call.

## Discover business logs

The explicit `index` wins; if omitted the MCP resolves the selected environment's configured default. If neither exists, ask the user or direct them to settings. Never silently expand to `*`. With a known index scope and applicable field evidence, run a bounded read-only search directly: listing indexes and getting mappings are not prerequisites. Report the actual environment and index, including whether explicit or default.

If a needed field or its behavior is unclear, consult applicable project code, scoped learned semantics, standards or prior verified queries; a small time-bounded sample can show observed fields and values. Inspect the actual time field, `app_name` for PerfLog versus `app` for StreamLog, and process/result fields. A sample does not establish field type, exact-match or aggregation support, or completeness; do not infer a `.keyword` suffix. When that remaining information is necessary for a reliable answer, obtain authoritative evidence from the scoped mapping if available or ask the user for the minimum field definition, sanitized sample, or mapping excerpt. Describe unresolved assumptions and do not calculate an unsupported result.

Before an actually necessary metadata request, inspect `list_log_environments`' optional `metadata_capabilities[environment]` entry. Its `index` is the configured default scope and `denied` entries identify the tool and observation/expiry time; an absent entry means unknown, not allowed. Do not repeat a denied operation for that scope during its cache lifetime. `ListIndexTool` and `IndexMappingTool` also apply scope-specific denial caching for explicit index scopes. The cache has a 24-hour lifetime and applies only when the stored profile has a versioned credential identity; an absent entry does not mean a metadata request previously succeeded. Inspect their structured `status` and `is_error`: `status=permission_denied` with `result=null` is a denial, even when the MCP call itself succeeded, not an empty index or mapping. `cached` indicates whether it came from a recorded denial. If permissions have changed or a user explicitly asks to recheck, use the operation's `force_refresh=true` to perform one fresh metadata request. A 403 for metadata does not imply search is denied; a failed or zero-shard search does not prove absence of data.

PerfLog may live in grouped/combined indexes rather than an index named `perf*`. A Kafka topic `perf_exchange_raw` is not an index name. The investigated UAT setup had combined indexes and a `type=perf_exchange` discriminator; treat this as an observed example, not a universal index naming rule. Use the actual index, type/topic and application dimensions from current evidence. Do not interpret denial of the guessed pattern `perf*` as proof the account cannot read any PerfLog.

## Which processes failed recently?

1. Establish the time window and app scope. If the user says “recently”, use a stated bounded window (for example 24 hours) unless context calls for a different one.
2. Search or aggregate by the service's `process_result=Fail`, grouped by `process`, `app_name`, error code and operation/message type where available. Use date min/max and a few `top_hits` samples. Include totals for the same population if calculating a failure proportion; do not divide failed events by unique tokens or by another service's totals.
3. Prefer `batch_search` for a summary aggregation and a small evidence query in the same environment. Each query takes `name`, optional `index`, `query_dsl`, and `size`; an omitted index resolves to that environment's configured default. Top-level `size=0` is suitable for aggregation-only queries. A field mapped directly as keyword uses its original name, not an invented `.keyword` suffix.
4. Check each result's `is_error`, `timed_out`, `_shards.failed`, `hits.total.relation`, and terms aggregation `sum_other_doc_count`/count error. Flag partial results, empty shards and truncated buckets. Do not count a sampled hit list as the full failure count.
5. Join representative PerfLog hits with `correlate_perflog(perflog_records=result.hits.hits, client=..., environment=..., start=..., end=..., include_details=true)`. The returned environment must match the source search. More than ten client/token pairs require bounded batches. Do not count one PerfLog and its StreamLog counterpart as two failed business operations.

For example, a service can log PerfLog `process=AccessEvent` while its StreamLog uses a more specific business process; inspect its operation/message type and correlated request to label the event. Process names need not be equal across the two logs. `UNKNOWN` business status is not automatically equivalent to standard `process_result=Fail`, and a later `DELIVERED` record may change the interpretation of earlier observations.

## Evidence without custom client scripts

- Single query: `SearchIndexTool(..., environment="uat")` → `result.hits.hits` or `result.aggregations`.
- Several related queries: `batch_search(queries=[...], environment="uat")` → inspect each named result.
- Payload chain: `correlate_perflog(..., environment="uat")`, then relevant `get_streamlog_detail(..., environment="uat")` if more detail is needed.
- Configuration/debugging: `list_log_environments`; use Structured Settings or `open_log_settings` for the shared configuration and the credentials action for secrets. New credentials are read on the next call. A host missing the newly installed tools needs plugin refresh, not a generated MCP bridge.

Present concise attributed findings directly in chat. Create evidence exports only for a requested report/export, and disclose their scope and masking limitations.
