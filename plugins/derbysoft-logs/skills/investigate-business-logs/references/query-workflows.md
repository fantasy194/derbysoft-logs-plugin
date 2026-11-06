# Direct MCP query workflows

These are tool arguments to compose in memory, not instructions to create files or scripts. Select one environment and carry its explicit name through every call.

## Discover business logs

The explicit `index` wins; if omitted the MCP resolves the selected environment's configured default. If neither exists, ask the user or direct them to settings. Never silently expand to `*`. When helpful, call `ListIndexTool` and `IndexMappingTool` for that same scope; inspect the actual time field, `app_name` for PerfLog versus `app` for StreamLog, the process/result fields and available exact-match mappings. Metadata access can be denied while search still works; if the user or verified earlier records give an index and fields, make a small time-bounded search and report the unverified mapping. Report the actual environment and index, including whether explicit or default.

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
