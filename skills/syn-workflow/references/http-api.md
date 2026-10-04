# Workflow HTTP API

The HTTP calls behind the `syn workflow` commands. Read this when an agent
needs structured output or the CLI is unavailable.

The same operations are HTTP calls against `$SYN_API_URL/api/v1`, with the
`Authorization` header that matches the credentials in use:

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/workflows?include_archived=false&page=1&page_size=50"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/workflows/<workflow-id>"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/workflows/<workflow-id>/runs"
curl -sf -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$SYN_API_URL/api/v1/workflows/<workflow-id>/execute" \
  -d '{"task": "Fix the auth timeout", "inputs": {"base_branch": "develop"}, "repos": ["owner/repo"]}'
```

| endpoint | notes |
|---|---|
| `GET /workflows` | query params `workflow_type`, `include_archived`, `page`, `page_size`, `order_by`. There is no free-text search parameter. Page with `page=N&page_size=100` until a page comes back short. |
| `GET /workflows/{id}` | the detail `syn workflow show` reads, including `input_declarations` and `phases` |
| `GET /workflows/{id}/runs` | the history `syn workflow status` reads |
| `POST /workflows/{id}/execute` | body `inputs` (string to string), `task`, `repos`. Returns `execution_id`, `workflow_id`, `status` (`started`), `message`. |

The HTTP path skips the CLI's pre-dispatch checks, so a direct `POST` will
start a run whose task or inputs are discarded without warning. Run
`syn workflow run ... --dry-run` first if you can.
