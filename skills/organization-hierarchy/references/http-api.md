# Organization, system and repo HTTP API

The routes behind `syn org`, `syn system` and `syn repo`, with their filters.
Read this when you need structured output, a filter the CLI does not
expose, or the one operation (deregistering a repo) that has no CLI
command.

Every command is an HTTP call against `$SYN_API_URL/api/v1`:

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/organizations"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/systems?organization_id=<org-id>"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/repos?unassigned=true"
curl -sf -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$SYN_API_URL/api/v1/repos/<repo-id>/assign" -d '{"system_id": "<system-id>"}'
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/systems/<system-id>/status"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/insights/overview"
```

| endpoint | notes |
|---|---|
| `/organizations`, `/organizations/{id}` | create, list, show, update, delete |
| `/systems`, `/systems/{id}` | list filter `organization_id`; plus `/status`, `/cost`, `/activity`, `/patterns`, `/history` |
| `/repos`, `/repos/{id}` | list filters `organization_id`, `system_id`, `provider`, `unassigned`; plus `/assign` (body `system_id`), `/unassign`, `/health`, `/cost`, `/activity`, `/failures`, `/sessions` |
| `DELETE /repos/{id}` | deregisters a repo; no CLI command. Refused (409) while it has active triggers |
| `/insights/overview`, `/insights/cost`, `/insights/contribution-heatmap` | deployment wide rollups across all organizations |

A refusal comes back as HTTP 409 with the reason in `detail`.
