# Trigger HTTP API

Every trigger route, and a complete `POST /triggers` body. Read this when
the CLI's simple case is not enough: input mapping, operators other than
`eq`, a name, or a different daily limit.

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
API="$SYN_API_URL/api/v1"
curl -sf -H "$AUTH" -H "Content-Type: application/json" -X POST "$API/triggers" -d '{
  "name": "review-new-prs",
  "event": "pull_request.opened",
  "repository": "owner/repo",
  "workflow_id": "<workflow-id>",
  "conditions": [
    {"field": "pull_request.draft", "operator": "eq", "value": "false"},
    {"field": "pull_request.base.ref", "operator": "eq", "value": "main"}
  ],
  "input_mapping": {
    "repository": "repository.full_name",
    "pr_number": "pull_request.number",
    "branch": "pull_request.head.ref"
  },
  "config": {"max_attempts": 3, "daily_limit": 20, "cooldown_seconds": 300}
}'
```

| endpoint | does |
|---|---|
| `POST /triggers` | register: `name`, `event`, `repository`, `workflow_id`, `conditions[]` (`field`, `operator`, `value` as a string), `input_mapping`, `config` (`max_attempts` default 3, `daily_limit` 20, `cooldown_seconds` 300) |
| `POST /triggers/presets/{preset_name}` | enable a preset: `repository`, optional `workflow_id` |
| `GET /triggers` | list; params `repository`, `status` |
| `GET /triggers/{id}` | `name`, `event`, `repository`, `workflow_id`, `status`, `fire_count`, `conditions`, `input_mapping`, `config`, `last_fired_at` |
| `GET /triggers/{id}/history` | `entries[]`: `fired_at`, `execution_id`, `event_type`, `pr_number`, `status`, `cost_usd`, `guard_name`, `block_reason`; param `limit` |
| `PATCH /triggers/{id}` | `{"action": "pause", "reason": "..."}` or `{"action": "resume"}` |
| `DELETE /triggers/{id}` | soft delete: the rule's status becomes `deleted`; it is not erased, and no route restores it |

The API accepts a `reason` when pausing; the CLI does not send one.
