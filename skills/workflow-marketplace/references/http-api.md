# HTTP endpoints used by marketplace work

The two workflow API routes that marketplace work touches. Read this when you
need structured output, or when you cannot use the CLI.

Registering a marketplace, searching and `info` have no HTTP API. They are
CLI operations on the local registry. The deployment side of an install is
the ordinary workflow API (see syn-workflow). Two calls are useful directly:

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
curl -sf -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$SYN_API_URL/api/v1/workflows/validate" \
  -d "$(jq -n --rawfile c workflow.yaml '{content: $c, filename: "workflow.yaml"}')"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/workflows/<workflow-id>/export?format=package"
```

| endpoint | notes |
|---|---|
| `POST /workflows/validate` | body `content`, `filename`. Returns `valid`, `name`, `workflow_type`, `phase_count`, `errors`, `warnings`. Cannot resolve `prompt_file`; validate a package with the CLI. |
| `GET /workflows/{id}/export` | `format` is `package` or `plugin`; what `syn workflow export` writes to disk |
