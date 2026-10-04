# Execution detail fields used in diagnosis

The fields of `GET /api/v1/executions/{id}` that attribute a failure, with
their values and how to read them. Read this during step 6 of the workflow,
after `syn execution show` has named the failing phase.

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/executions/<execution-id>"
```

| field | values | read it as |
|---|---|---|
| `failure_classification` | `platform`, `task`, `correct_refusal`, `unclassified` | the platform's own attribution |
| `reported_failure_reason` | `task`, `platform`, `refused`, `unknown` | what the agent said about its own failure |
| `reported_side_effects` | `none`, `succeeded`, `denied`, `failed` | `denied` means a missing permission |
| `deliverable_produced` | true or false | whether the work exists despite the status |
| `error_message` | text | the execution-level error |
| `phases[].error_message` | text | the failing phase's own error |
| `phases[].session_id`, `phases[].agent_session_ids` | ids | where to look next |
| `phases[].artifact_id`, `artifact_ids` | ids | the phase output, if any was stored |
