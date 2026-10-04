# Where the corpus comes from

The endpoints that supply execution records, session metadata and transcript
bodies, with the fields each returns. Read this at the "pull the corpus" step.
These are the deployed product surface; if one has moved, only this file
needs editing.

## Execution records, from the Syntropic137 API

```
GET /api/v1/executions?page_size=100
    -> executions[]: workflow_execution_id, workflow_id, status, total_cost_usd,
       total_tokens, duration_seconds, tool_call_count, completed_phases,
       total_phases, error_message, started_at

GET /api/v1/executions/{id}
    -> phases[]: name, status, model, cost_usd, duration_seconds,
       error_message, artifact_id, operations[]
```

`phases[].operations` is the recorded tool use: the observation, as opposed
to the agent's own account of what it did. `GET /api/v1/artifacts/{id}`
returns a phase's written output.

## Session transcripts, from the session store

```
GET  /v1/sessions/corpus?limit=&cursor=       metadata for analytics, IDs and facets
GET  /v1/sessions/search?tags=&limit=&cursor= keyset search; deployment is a TAG
POST /v1/sessions/raw/batch                   {"session_ids": [...]}, max 10 per call
GET  /status                                  per-machine totals and staleness
```

Sessions carry tags of the form `deployment:<name>`, `workflow_id:<id>`,
`phase_id:<id>`, `execution_id:<id>`. Filter the deployment by **tag**:
`origin_environment` is the container, not the deployment, and filtering on it
returns nothing.
