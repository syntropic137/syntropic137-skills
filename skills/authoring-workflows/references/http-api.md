# Validating a workflow over HTTP

The HTTP call behind `syn workflow validate` for a single file. Read this when
an agent needs structured validation output or the CLI is unavailable.

Validate one self contained file:

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
curl -sf -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$SYN_API_URL/api/v1/workflows/validate" \
  -d "$(jq -n --rawfile c workflow.yaml '{content: $c, filename: "workflow.yaml"}')"
```

The response has `valid`, `name`, `workflow_type`, `phase_count`, `errors`
and `warnings`. It cannot resolve `prompt_file`; validate packages with the
CLI (`syn workflow validate ./my-package/`).
