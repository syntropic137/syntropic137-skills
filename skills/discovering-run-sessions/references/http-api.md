# Session inventory HTTP API

The routes behind `syn execution sessions` and `syn execution transcript`,
and the optional remote replica. Read this when you need the raw routes or
the CLI is unavailable.

All of the workflow is also plain HTTP against `$SYN_API_URL/api/v1`, with
the same credential as the rest of the API:

| endpoint | returns |
|---|---|
| `GET /executions/{id}/session-inventory` | `run`, `summary`, `snapshot` (with `snapshot_id`), `reconstruction_status` |
| `GET /executions/{id}/session-inventory/{snapshot_id}/{kind}` | one page of a section: `items`, `item_keys`, `next_cursor`, and on capture pages `body_overrides` and `capture_hashes`. Kinds `node`, `membership`, `edge`, `capture`, `gap`, `binding`, `retraction`. Params `limit` (up to 500), `cursor`, `phase_id`, `attempt_id`. Repeat with `cursor=<next_cursor>` until it is null; on `410` `cursor_expired`, restart from the summary |
| `GET /executions/{id}/session-inventory/{snapshot_id}/nodes/{node_key}` | one node by key |
| `GET /executions/{id}/session-transcripts/{archive_sha256}?harness=<h>&native_id=<id>` | one transcript: `status`, `content_format`, `size`, `content_base64`, `conversation` |

The reconcile, backfill, revocation and deletion routes change state. Do not
call them unless the user asks: deleting a transcript erases its bytes for
every run that shares them and cannot be undone.

## Remote replica

When `summary.remote_replication` is `enabled`, the inventory is also
replicated to a central SeshMagic store, queried with that store's own read
token by `source_instance_id` and `execution_id` (both in `run`). The replica
can trail the local inventory. Public guide:
https://docs.syntropic137.com/docs/guide/session-discovery
