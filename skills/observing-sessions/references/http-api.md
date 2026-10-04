# Sessions, observability and costs HTTP API

The routes behind `syn sessions`, `syn observe`, `syn costs`, `syn metrics`
and `syn insights`, with their parameters and fields. Read this when you need
structured output, a tool's input and output previews, or the CLI is
unavailable.

All of the workflow is also plain HTTP against `$SYN_API_URL/api/v1`. Send
the `Authorization` header that matches your credentials:

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
API="$SYN_API_URL/api/v1"
curl -sf -H "$AUTH" "$API/sessions?execution_id=<execution-id>&page=1&page_size=50"
curl -sf -H "$AUTH" "$API/sessions/<session-id>"
curl -sf -H "$AUTH" "$API/costs/executions/<execution-id>"
```

| endpoint | returns |
|---|---|
| `GET /sessions` | a page of platform sessions; params `workflow_id`, `execution_id`, `status`, `statuses`, `started_after`, `started_before`, `q`, `page`, `page_size`. Each has `parent_session_id` and `root_session_id` for delegation |
| `GET /sessions/{id}` | the session and its `operations[]`: `operation_type`, `timestamp`, `duration_seconds`, `success`, `error_message`, token counts, `tool_name`, `tool_use_id`, `tool_input`, `tool_output` |
| `GET /observability/sessions/{id}/tools` | `executions[]`: `operation_type`, `tool_name`, `timestamp`, `duration_ms`, `success`, `error_message`; param `limit` |
| `GET /observability/sessions/{id}/tokens` | `input_tokens`, `output_tokens`, `total_tokens`, `cache_creation_tokens`, `cache_read_tokens`, `total_cost_usd` |
| `GET /costs/sessions/{id}` | `total_cost_usd`, `cost_by_model`, `cost_by_tool`, `tokens_by_tool`, `unpriced_observation_count`, `unmeasured_fields` |
| `GET /costs/executions/{id}` | `total_cost_usd`, `cost_by_phase`, `unpriced_by_phase`, `cost_by_model`, `cost_by_tool`, `unpriced_observation_count`, `is_complete` |
| `GET /costs/sessions`, `GET /costs/executions`, `GET /costs/summary` | lists and the deployment-wide summary |
| `GET /metrics` | aggregated metrics; param `workflow_id` |
| `GET /insights/overview`, `/insights/cost`, `/insights/contribution-heatmap` | the `syn insights` views |

`tool_input` and `tool_output` on each operation are previews cut to 500
characters, recorded when the operation was captured; they are not the full
tool payload. `tool_input` is returned as an object when the preview parses
as JSON, and otherwise wrapped as `{"raw": "<preview>"}`.

`unmeasured_fields` names fields that hold a default rather than a reading,
such as `compute_cost_usd`: report those as unknown, not zero.
