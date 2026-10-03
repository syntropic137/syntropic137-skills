---
name: discovering-run-sessions
description: Use when you need every agent session of one Syntropic137 workflow run - not just the platform sessions but the delegates agents started inside their workspaces and the native transcripts each harness recorded - with how they relate, which failed or never launched, whether the list is known to be complete, and the transcripts themselves. Trigger phrases include "all sessions of exec-...", "how many agents ran", "what did the delegates do", "which sub-agent failed", "did every delegate finish", "pull the transcripts of this run", "is the session list complete", "coverage reconciled", "session inventory", "syn execution sessions", "syn execution transcript". Do NOT use for what one platform session cost or which tools it called (use observing-sessions), for cancelling, resuming or diagnosing an execution's phases (use execution-control), or for lessons across many finished runs (use mining-session-logs).
---

# Discovering every session of a Syntropic137 run

A workflow run is rarely one agent. A phase agent can delegate to `claude -p`
or `codex exec` inside its workspace, delegates can start children of their
own, and a resume continues earlier work. `syn sessions list` shows only the
**platform** sessions. The **session inventory** shows every session of a run,
how they relate, which transcripts were captured, and whether the list is
known to be complete.

The mistake this skill exists to prevent is concluding "the run had N agents"
or "nothing failed" from a list nobody has shown to be complete. **A session
list is only complete when its coverage is `reconciled` and the read covered
every section. Say which state it is in, every time.**

## Outcomes we are looking for

### Outcome 1: every count carries its coverage

- *Signal:* a statement about how many agents ran, or that none failed, quotes
  the server's coverage line alongside it.
- *Signal:* a partial view is labelled partial, with its coverage state and
  the gaps that make it partial.

### Outcome 2: every failed, missing or unlaunched delegate is named

- *Signal:* each gap that names a session is mapped to that session, with its
  harness, its id and its parent.

### Outcome 3: an unavailable transcript is reported as unavailable

- *Signal:* a transcript that could not be read is reported with the status
  the server gave, never as "the agent did nothing".

## Before you start

Every command talks to one deployment. Check which one:

```bash
syn config show     # SYN_API_URL and whether credentials are set
syn health
```

`SYN_API_URL` defaults to `http://localhost:8137`. Credentials are
`SYN_API_TOKEN` (bearer) or `SYN_API_USER` + `SYN_API_PASSWORD` (basic).

You need the execution id (`exec-...`). The examples use `jq`.

## The model

| term | meaning |
|---|---|
| **node** | one session, in one of three namespaces: `platform` (a session the platform created and bills; `syn sessions show` works on it), `invocation` (an agent process registered as launched inside a workspace, such as a delegate), `transcript` (a harness's own native session, with a `harness`) |
| **binding** | says a platform session or invocation and a native transcript are the same piece of work. Count them once |
| **membership** | places a node in a phase and attempt |
| **edge** | parent to child, `relation` `spawn` (started a delegate), `resume` (continued a conversation) or `fork` (branched) |
| **capture** | a receipt that a transcript was archived, with its `availability` and, for a local present body, `archived_byte_hash` |
| **gap** | a known hole: a `reason` and the `node_keys` it affects. No keys means it applies to the whole run |
| **coverage** | `summary.coverage_state`, the verdict on completeness |

A native transcript id is never a platform session id. Never pass one to
`syn sessions show`.

Each edge, membership and binding also carries a `confidence`: `registered`,
`corroborated`, `candidate` or `conflicting`.

## Coverage

| `coverage_state` | what you may conclude |
|---|---|
| `reconciled` | complete, when `summary.complete` is true |
| `open` | not complete: the run is running, or still settling after it ended (by default for up to 30 minutes). Say so and check again later |
| `missing` | settled, with known sessions or captures unaccounted for. The gaps name them |
| `conflicting` | the evidence disagrees. Report the conflicting gaps; do not pick a side |
| `unsupported` | completeness cannot be proven, for example a run that was not instrumented |
| `unknown` | no coverage contract, or no published revision yet |

`summary.complete` is the server's verdict: coverage `reconciled` on the
current revision. The CLI's top-level `complete` adds that **this read** saw
every section of that revision, unfiltered. A filtered or single-section read
is partial even when the run is reconciled.

## Principles

- **Print the server's lines, don't recompute them.** `counts_display`,
  `coverage_display` and `follow_up_command` are written by the server so every
  client says the same thing.
- **Read one revision.** `--all` pins a revision and reads every page of every
  section from it. Mixing pages from different reads mixes revisions.
- **Reads are read-only.** Reading the inventory never triggers capture or
  reconstruction.
- **Report unfamiliar gap reasons.** The vocabulary is open; an unknown reason
  is still a gap.

## Anti-patterns

- **Counting with `syn sessions list`.** It omits delegates and native
  transcripts.
- **Reading without `--all`.** You get the first page of one section, and the
  CLI tells you the listing is partial.
- **Counting a binding twice.** A platform session and the transcript bound to
  it are one piece of work.
- **Writing to the inventory unasked.** The reconcile, backfill, revocation and
  deletion routes change state. Deleting a transcript erases its bytes for
  every run that shares them and cannot be undone. Do not call them unless the
  user asks.

## The procedure

### 1. Read the summary

```bash
syn execution show <execution-id>
```

The output ends with `Session inventory:` (the counts), `Coverage:` (with
`(incomplete)` when it is not complete) and `Details:` (the exact follow-up
command). Quote these lines.

### 2. Read every session from one revision

```bash
syn execution sessions <execution-id> --all --json > inventory.json
```

Read first: `summary.coverage_state`, `summary.coverage_display`,
`summary.counts_display`, `complete`, `coverage_complete`,
`traversal_complete`, `pending_sections`, `gaps`. The pages are under
`pages[]`, each with a `kind`, `items[]` and `item_keys[]`.

For a human view, `syn execution sessions <execution-id> --all` groups
sessions by phase and attempt, then unlinked sessions, then gaps. `--phase`
and `--attempt` narrow it to one phase or attempt (a partial read);
`--kind <section>` reads one section.

For automation that must not act on a partial list, add `--require-complete`:
the command prints what it read, then exits nonzero unless coverage is
`reconciled`, the revision is current, and every section was read
unfiltered.

### 3. Name the failed, missing and unlaunched sessions

| gap `reason` | meaning |
|---|---|
| `invocation_failed`, `invocation_cancelled` | the process ended abnormally |
| `invocation_launch_failed`, `invocation_launch_failed_<cause>` | it never started. Causes include `process_start_failed`, `codex_sandbox_unavailable`, `native_tool_failed`, `native_tool_interrupted`, `capture_hook_failed`, `hook_watchdog`, `capture_hook_unreachable` |
| `invocation_transport_failed_before_announce` | failed before announcing itself; not known to have run |
| `invocation_running`, `invocation_pending` | no outcome yet. Provisional while coverage is `open` |
| `invocation_unsettled_at_seal`, `capture_unsettled_at_seal`, `child_context_unresolved_at_seal`, `parentage_unresolved_at_seal` | still unsettled when the settlement deadline passed |
| `expected_body_unavailable` | an expected session has no present transcript |
| `conflicting_*`, `lineage_cycle`, `unresolved_parentage`, `unverified_invocation_context` | identity, parentage or attribution evidence disagrees or is unverified |
| `no_host_registration` | the run was not instrumented; coverage `unsupported` |

Map each gap to the sessions it names. On node pages, `item_keys[i].node_key`
is the key of `items[i]`:

```bash
jq -r '
  ([.pages[] | select(.kind == "node") | . as $p
    | range(0; $p.items | length)
    | {key: $p.item_keys[.].node_key, value: $p.items[.].ref}] | from_entries) as $nodes
  | .gaps[]? | .reason as $r
  | if (.node_keys | length) == 0 then "\($r)\t(run-level)"
    else .node_keys[] | "\($r)\t\($nodes[.].kind // "?"):\($nodes[.].harness // "-")\t\($nodes[.].local_id // .)"
    end' inventory.json
```

A key not on any page you read resolves with
`GET /executions/{id}/session-inventory/{snapshot_id}/nodes/{node_key}`.

### 4. Follow the lineage

```bash
jq -r '.pages[] | select(.kind == "edge") | .items[]
  | "\(.parent.kind):\(.parent.local_id) -[\(.relation)]-> \(.child.kind):\(.child.local_id) (\(.confidence))"' inventory.json
```

Memberships (`kind == "membership"`) give each node's `phase_id` and
`attempt_id`. Together they are the delegation tree.

### 5. Read the transcripts

A capture with `destination` `local` and `availability` `present` carries
`archived_byte_hash`, which is the read key:

```bash
syn execution transcript <execution-id> <harness> <native-id> <archived-byte-hash> --json
```

`--json` returns the normalized `conversation` (read this) and the bytes in
base64; `--raw` writes the exact archived bytes. A body whose status is
`not_captured`, `missing`, `expired`, `deleted` or `too_large` exits nonzero
with that status; a revoked body is refused. Report it as unavailable.

A capture receipt is history. In the human view, `recorded=` is what the
receipt said and `current=` is the body's state now (`expired`, `deleted` or
`withheld` override it). A remote receipt carries a `sha256:...` content hash,
which the local transcript route cannot read.

Every local transcript of a run:

```bash
EXEC=<execution-id>
mkdir -p transcripts
jq -c '.pages[] | select(.kind == "capture") | .items[]
  | select((.destination // "local") == "local" and .availability == "present")
  | {harness: .node.harness, native: .node.local_id, sha: .archived_byte_hash}' inventory.json | sort -u |
while IFS= read -r rec; do
  harness=$(jq -r .harness <<<"$rec"); native=$(jq -r .native <<<"$rec"); sha=$(jq -r .sha <<<"$rec")
  syn execution transcript "$EXEC" "$harness" "$native" "$sha" --json > "transcripts/$sha.json" \
    || echo "unavailable: $rec"
done
```

### 6. Report

Quote the coverage line first. Then, per phase: which agents ran, how each
ended, and its parent. Then every gap, mapped to its session. For what one
platform session did or cost, hand off to the observing-sessions skill. To
turn a set of finished runs into lessons, use mining-session-logs.

## Recommended tools and practices (as of 2026-10-03)

All of the above is also plain HTTP against `$SYN_API_URL/api/v1`, with the
same credential as the rest of the API:

| endpoint | returns |
|---|---|
| `GET /executions/{id}/session-inventory` | `run`, `summary`, `snapshot` (with `snapshot_id`), `reconstruction_status` |
| `GET /executions/{id}/session-inventory/{snapshot_id}/{kind}` | one page of a section: `items`, `item_keys`, `next_cursor`, and on capture pages `body_overrides` and `capture_hashes`. Kinds `node`, `membership`, `edge`, `capture`, `gap`, `binding`, `retraction`. Params `limit` (up to 500), `cursor`, `phase_id`, `attempt_id`. Repeat with `cursor=<next_cursor>` until it is null; on `410` `cursor_expired`, restart from the summary |
| `GET /executions/{id}/session-inventory/{snapshot_id}/nodes/{node_key}` | one node by key |
| `GET /executions/{id}/session-transcripts/{archive_sha256}?harness=<h>&native_id=<id>` | one transcript: `status`, `content_format`, `size`, `content_base64`, `conversation` |

`syn execution sessions <execution-id> --refresh` schedules a local
reconstruction and reports its job. It is the one inventory command that
writes; use it when the inventory is stale and the user wants it rebuilt.

When `summary.remote_replication` is `enabled`, the inventory is also
replicated to a central SeshMagic store, queried with that store's own read
token by `source_instance_id` and `execution_id` (both in `run`). The replica
can trail the local inventory. Public guide:
https://docs.syntropic137.com/docs/guide/session-discovery

Run `syn execution sessions --help` and `syn execution transcript --help` for
the flags of the installed CLI version.
