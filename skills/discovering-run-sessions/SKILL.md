---
name: discovering-run-sessions
description: Use when you need every agent session of one Syntropic137 workflow run - not just the platform sessions but the delegates agents started inside their workspaces and the native transcripts each harness recorded - with how they relate, which failed or never launched, whether the list is known to be complete, and the transcripts themselves. Trigger phrases include "all sessions of exec-...", "find every session of this execution", "how many agents ran", "what did the delegates do", "which sub-agent failed", "did every delegate finish", "pull the transcripts of this run", "is the session list complete", "coverage reconciled", "session inventory", "syn execution sessions", "syn execution transcript". Do NOT use for what one platform session cost or which tools it called (use observing-sessions), for cancelling, resuming or diagnosing an execution's phases (use execution-control), or for lessons across many finished runs (use mining-session-logs).
metadata:
  version: "1.0.0"
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

## When to Use

- You need every session of one run, including delegates and native
  transcripts, and how they relate.
- You need to know which delegate failed, never launched, or is unaccounted
  for.
- You need the transcripts of a run.
- You need to know whether a run's session list is complete.

## When NOT to Use

- You want what one platform session did or cost, or its tool calls: use
  observing-sessions.
- You want to cancel, resume or diagnose an execution's phases: use
  execution-control.
- You want lessons across many finished runs: use mining-session-logs.

## Input

- **Deployment** (required, environment): `SYN_API_URL`, default
  `http://localhost:8137`. Credentials are `SYN_API_TOKEN` (bearer) or
  `SYN_API_USER` + `SYN_API_PASSWORD` (basic). Check with `syn config show`
  and `syn health`.
- **Execution id** (`exec-...`, required).
- **Narrowing** (optional, makes the read partial): `--phase`, `--attempt`,
  `--kind <section>`.
- **`--require-complete`** (optional flag): for automation that must not act
  on a partial list.
- **`jq`** (tool, optional): the examples use it.

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

The inventory's vocabulary (node, binding, membership, edge, capture, gap,
confidence) is defined in [references/model.md](references/model.md). Two
rules from it matter on every read: a platform session and the transcript
bound to it are one piece of work, so count them once; and a native
transcript id is never a platform session id, so never pass one to
`syn sessions show`.

## Workflow

1. Check which deployment you are talking to with `syn config show` and
   `syn health`.

2. Read the summary with `syn execution show <execution-id>`. The output ends
   with `Session inventory:` (the counts), `Coverage:` (with `(incomplete)`
   when it is not complete) and `Details:` (the exact follow-up command).
   Quote these lines: `counts_display`, `coverage_display` and
   `follow_up_command` are written by the server so every client says the
   same thing, so print them rather than recomputing them.

3. Read every session from one revision:

   ```bash
   syn execution sessions <execution-id> --all --json > inventory.json
   ```

   `--all` pins a revision and reads every page of every section from it;
   mixing pages from different reads mixes revisions, and reading without
   `--all` gets the first page of one section. Read first:
   `summary.coverage_state`, `summary.coverage_display`,
   `summary.counts_display`, `complete`, `coverage_complete`,
   `traversal_complete`, `pending_sections`, `gaps`. The pages are under
   `pages[]`, each with a `kind`, `items[]` and `item_keys[]`. For a human
   view, `syn execution sessions <execution-id> --all` groups sessions by
   phase and attempt, then unlinked sessions, then gaps. With
   `--require-complete` the command prints what it read, then exits nonzero
   unless coverage is `reconciled`, the revision is current, and every
   section was read unfiltered. Reading the inventory never triggers capture
   or reconstruction.

4. Name the failed, missing and unlaunched sessions by mapping each gap to
   the sessions it names. On node pages, `item_keys[i].node_key` is the key
   of `items[i]`:

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

   What each gap `reason` means is in
   [references/gap-reasons.md](references/gap-reasons.md). The vocabulary is
   open: report an unfamiliar reason as a gap. A key not on any page you read
   resolves with
   `GET /executions/{id}/session-inventory/{snapshot_id}/nodes/{node_key}`.

5. Follow the lineage. Edges give parent to child; memberships
   (`kind == "membership"`) give each node's `phase_id` and `attempt_id`.
   Together they are the delegation tree:

   ```bash
   jq -r '.pages[] | select(.kind == "edge") | .items[]
     | "\(.parent.kind):\(.parent.local_id) -[\(.relation)]-> \(.child.kind):\(.child.local_id) (\(.confidence))"' inventory.json
   ```

6. Read the transcripts. A capture with `destination` `local` and
   `availability` `present` carries `archived_byte_hash`, which is the read
   key:

   ```bash
   syn execution transcript <execution-id> <harness> <native-id> <archived-byte-hash> --json
   ```

   `--json` returns the normalized `conversation` (read this) and the bytes
   in base64; `--raw` writes the exact archived bytes. A body whose status is
   `not_captured`, `missing`, `expired`, `deleted` or `too_large` exits
   nonzero with that status; a revoked body is refused. Report it as
   unavailable. To fetch every local transcript of a run, and to read a
   capture receipt's `recorded=` and `current=` states, see
   [references/transcripts.md](references/transcripts.md).

7. Report. Quote the coverage line first. Then, per phase: which agents ran,
   how each ended, and its parent. Then every gap, mapped to its session. For
   what one platform session did or cost, hand off to observing-sessions. To
   turn a set of finished runs into lessons, use mining-session-logs.

## Output

- A report that opens with the server's coverage line and states whether the
  list is complete, partial, or unprovable.
- Per phase and attempt: each agent, its harness, its id, its parent, and
  how it ended.
- Every gap mapped to the sessions it names, or marked run-level.
- Optionally `inventory.json` and a `transcripts/` directory of the
  transcripts that were present, with every unavailable one listed with its
  status.
- Nothing written to the inventory unless the user asked for it.

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

## Recommended tools and practices (as of 2026-10-04)

### Outcome: every count carries its coverage

- **`syn execution sessions --all --json`.** Ladders up by reading every
  section from one pinned revision, so the count and its coverage describe
  the same data. Tradeoffs: one large file per run.
- **`--require-complete` in automation.** Ladders up by turning a partial
  list into a nonzero exit instead of a silent undercount.

### Outcome: every failed, missing or unlaunched delegate is named

- **The gap-to-node `jq` mapping in step 4.** Ladders up by attaching every
  gap to a harness, an id and a kind. Tradeoffs: it only resolves keys on
  pages you read; use the single-node route for the rest.
- **[references/gap-reasons.md](references/gap-reasons.md).** Ladders up by
  translating each reason into "ended abnormally", "never started", "no
  outcome yet" or "evidence disagrees".

### Outcome: an unavailable transcript is reported as unavailable

- **`syn execution transcript --json`.** Ladders up by exiting nonzero with
  the body's status, which is what goes in the report.
- **`syn execution sessions <execution-id> --refresh`** schedules a local
  reconstruction and reports its job. Ladders up by turning a transcript
  that is unavailable only because the inventory is stale into one that can
  be read. Tradeoffs: it is the one inventory command that writes; use it
  when the inventory is stale and the user wants it rebuilt.

The HTTP routes, and the optional remote replica, are in
[references/http-api.md](references/http-api.md). Run
`syn execution sessions --help` and `syn execution transcript --help` for the
flags of the installed CLI version.

## References

- [references/model.md](references/model.md): node, binding, membership,
  edge, capture, gap and confidence. Read when an inventory field is
  unfamiliar.
- [references/gap-reasons.md](references/gap-reasons.md): every gap reason
  and what it means. Read during step 4.
- [references/transcripts.md](references/transcripts.md): capture receipts
  versus current body state, and a loop that fetches every local transcript.
  Read during step 6.
- [references/http-api.md](references/http-api.md): the inventory and
  transcript routes, paging, and the remote replica. Read when the CLI is
  unavailable.

## Continual improvement

File drift, gaps, or proposed updates at
https://github.com/syntropic137/syntropic137-skills/issues
