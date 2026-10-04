# Execution HTTP API

The HTTP routes behind `syn execution` and `syn control`. Read this when you
need structured output or the CLI is unavailable.

All of the workflow is also plain HTTP against `$SYN_API_URL/api/v1`. Send
the `Authorization` header that matches your credentials:

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
API="$SYN_API_URL/api/v1"
curl -sf -H "$AUTH" "$API/executions?status=running&page=1&page_size=50"
curl -sf -H "$AUTH" "$API/executions/<execution-id>"
curl -sf -H "$AUTH" "$API/executions/<execution-id>/state"
curl -sf -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$API/executions/<execution-id>/cancel" -d '{"reason": "wrong repository"}'
curl -sf -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$API/executions/<execution-id>/resume" \
  -d '{"override_cancellation": false, "acknowledge_external_effects": true}'
```

| endpoint | returns |
|---|---|
| `GET /executions` | a page of executions; params `status`, `statuses`, `page`, `page_size` |
| `GET /executions/{id}` | the full detail described in [diagnosis-fields.md](diagnosis-fields.md) |
| `GET /executions/{id}/state` | `execution_id` and `state` only |
| `GET /executions/{id}/session-inventory` | the session inventory behind `syn execution sessions` |
| `GET /workflows/executions/active` | executions currently active |
| `POST /executions/{id}/cancel` | `success`, `execution_id`, `state`, `message`, `error` |
| `POST /executions/{id}/resume` | `parent_execution_id`, `execution_id`, `resume_phase_id`, `inherited_phase_ids`, `cancellation_overridden`, `external_effects_acknowledged` |

There is no `/executions/{id}/status` route; use `/state` for the bare state
or the detail route for everything else.

`POST /executions/{id}/inject` and `syn control inject` exist and answer
success, but the message is not delivered to the running agent as of
2026-10-03. Do not use them to steer a run, and do not report a run as
steered because inject returned success.
