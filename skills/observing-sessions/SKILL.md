---
name: observing-sessions
description: Use when working out what a Syntropic137 agent session did, why it cost what it cost, or why it failed - its operations log, tool timeline, token and cache breakdown, cost by model, tool and phase, and platform-wide cost and activity. Trigger phrases include "why was this run expensive", "what did the agent do", "show the tool calls", "token usage of this session", "cache hit rate", "cost breakdown", "which phase cost the most", "why did this session fail", "cost shows unpriced", "syn sessions", "syn observe", "syn costs", "syn metrics", "syn insights". Do NOT use for listing every session of a run including delegates and native transcripts (use discovering-run-sessions), for cancelling, resuming or reading an execution's phases (use execution-control), or for lessons across many finished runs (use mining-session-logs).
---

# Observing Syntropic137 sessions and costs

A session is one headless agent invocation in one workspace: `claude -p` or
`codex exec`, depending on the harness the phase declared. A three-phase
workflow run starts three platform sessions, and phases of one run can use
different harnesses. This skill reads what a session did, what it cost, and
where the cost went.

Two mistakes dominate. The first is answering "why was it expensive" from the
total alone, when the breakdowns that explain it (by phase, by model, by tool,
cached versus uncached) are one command away. The second is reading a cost of
`$0` or a short total as cheap work, when it can mean the platform had no rate
for the model that ran. **A cost is a reading with a coverage, and the
coverage is part of the answer.**

## Outcomes we are looking for

### Outcome 1: every cost claim names where the cost went

- *Signal:* "this run was expensive" is followed by the phase, the model and
  the tools that carried the cost, each with its figure.
- *Signal:* cache behaviour is stated from the cache read and cache write
  token counts, not guessed.

### Outcome 2: incomplete costs are reported as incomplete

- *Signal:* a cost the CLI shows as `unpriced` or `>=$X (partial)` is
  reported that way, with the unpriced observation count, never rounded to a
  dollar figure.

### Outcome 3: a failure is explained from the session's own record

- *Signal:* the explanation names the operation where the session went wrong,
  its type (for example a failed tool call or a `tool_blocked` operation) and
  its error message.

## Before you start

Every command talks to one deployment. Check which one:

```bash
syn config show     # SYN_API_URL and whether credentials are set
syn health
```

`SYN_API_URL` defaults to `http://localhost:8137`. Credentials are
`SYN_API_TOKEN` (bearer) or `SYN_API_USER` + `SYN_API_PASSWORD` (basic).

You need a session id or an execution id. If you only have a workflow, list
its runs with `syn workflow status <workflow-id>`, or use the execution-control
skill to find the execution.

## What each view answers

| question | command | what it shows |
|---|---|---|
| what did the agent do, step by step | `syn sessions show <session-id>` | status, provider, model, tokens, cost, error, and the operations log (type, tool, success) |
| which tools ran, in order, and how long each took | `syn observe tools <session-id>` | time, tool, duration, ok or error |
| where did the tokens go | `syn observe tokens <session-id>` | input, output, total, cache creation, cache read, estimated cost |
| what did one session cost and why | `syn costs session <session-id>` | cost with coverage, tokens, cache, tool calls, turns, duration, cost by model, cost by tool |
| what did one execution cost and why | `syn costs execution <execution-id>` | cost with coverage, sessions, tokens, cache, duration, cost by phase, model and tool |
| which sessions or runs cost most | `syn costs sessions [-e <execution-id>]`, `syn costs executions`, `syn costs summary` | per-row costs; the summary adds top models and top sessions |
| per-phase totals for a workflow | `syn metrics show [-w <workflow-id>]` | workflows, sessions, tokens, cost, artifacts, and a phase table |
| deployment-wide picture | `syn insights overview`, `syn insights cost`, `syn insights heatmap [-d <days>]` | systems and repos with health and active executions; cost by repository and model; daily activity |

`syn sessions list` shows **platform** sessions only, filtered with
`--execution <id>`, `-w/--workflow <id>`, `-s/--status <status>` and
`-n/--limit`. Session statuses are `running`, `completed`, `failed` and
`cancelled`. Delegates an agent starts inside its workspace and the harness's
own transcripts are not in this list; for those, use the
discovering-run-sessions skill.

## Principles

- **Start from the execution, then narrow.** `syn costs execution` gives cost
  by phase; the expensive phase's session is where to look next.
- **The tool timeline has no inputs or outputs.** To see what a tool was
  called with and what it returned, read the operations of the session over
  the API (below): each carries `tool_name`, `tool_use_id`, `tool_input` and
  `tool_output`.
- **Cost coverage travels with the number.** Quote the CLI's `unpriced` or
  `(partial)` marker, and the unpriced observation count, every time.
- **Telemetry depth differs by harness.** Hook events, subagent tracking and
  TodoWrite are recorded for claude sessions only. A codex session's record is
  thinner by construction: its tool timeline is mapped from codex events
  (`command_execution` appears as `Bash`, `file_change` as `Edit`). A sparse
  codex timeline is not a sign of failure.

## Anti-patterns

- **Treating `$0` as free.** When observations had no rate for their model,
  the CLI shows `unpriced` (nothing could be priced) or `>=$X (partial)` (a
  lower bound). Tokens are still counted.
- **Looking for blocked tools in `syn observe tools`.** It shows ok or error.
  A blocked call is an operation of type `tool_blocked` in
  `syn sessions show`.
- **Passing a workflow id to `syn costs execution`.** It takes an execution
  id.
- **Counting a run's agents with `syn sessions list`.** It omits delegates and
  native transcripts.
- **Comparing models by alias.** `cost_by_model` is keyed by the model id the
  harness reported. Cost whose model no harness reported is under
  `unattributed-model`.

## The procedure

### 1. Why was this run expensive?

```bash
syn costs execution <execution-id>
```

Read, in order:

1. **Coverage.** If the cost is `unpriced` or `(partial)`, say so first. The
   API's `unpriced_by_phase` names the phases whose cost is unknown: a phase
   listed there and absent from `cost_by_phase` cost an unknown amount.
2. **Cost by phase.** The phase that carries the cost.
3. **Cost by model.** A top-tier model doing shallow work is the most common
   avoidable cost.
4. **Cost by tool.** Which tools the money went through.

Then take the expensive phase's session id (from `syn sessions list
--execution <execution-id>`, or `phases[].session_id` in
`GET /executions/{id}`) and read:

```bash
syn costs session <session-id>
syn observe tokens <session-id>
```

High cache read tokens relative to cache creation means the session reused
its context. Low cache reads beside high input tokens means it reloaded
context on many turns: large file reads or long command output repeated
across turns. The session cost's `tokens_by_tool` (API only) shows which tools
the tokens were attributed to; it is an estimate.

### 2. What did this session do?

```bash
syn sessions show <session-id>
syn observe tools <session-id>                # --limit, default 100
```

The operations log is the whole record: messages, tool starts and
completions, blocked tools, thinking, errors. The tool timeline is the same
tool calls with timing, for finding the slow step.

### 3. Why did this session fail?

1. `syn sessions show <session-id>`: the `Error:` line, then the last
   operations before it. Look for operations that did not succeed and for
   `tool_blocked`.
2. `syn observe tools <session-id>`: tools that ended in `error`, and
   durations that point to a hang.
3. The tool's own input and output, from the operations over the API.
4. The phase's error and the execution's failure classification: use the
   execution-control skill.

### 4. Why does the cost say unpriced?

The platform records no dollar figure for work on a model it has no rate for,
rather than a wrong one. On codex phases this happens when the phase names a
model the platform does not price; a codex phase that left its model unset is
given the platform's default codex model when the workflow is installed, and
is priced as that. Codex itself reports no vendor cost, so the platform's
figure is computed from tokens. Report the token counts, the unpriced
observation count, and the model the session reported (`syn sessions show`,
`Model:`).

## Recommended tools and practices (as of 2026-10-03)

All of the above is also plain HTTP against `$SYN_API_URL/api/v1`. Send the
`Authorization` header that matches your credentials:

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
API="$SYN_API_URL/api/v1"
curl -sf -H "$AUTH" "$API/sessions?execution_id=<execution-id>&page=1&page_size=50"
curl -sf -H "$AUTH" "$API/sessions/<session-id>"
curl -sf -H "$AUTH" "$API/costs/executions/<execution-id>"
```

| endpoint | returns |
|---|---|
| `GET /sessions` | a page of platform sessions; params `workflow_id`, `execution_id`, `status`, `statuses`, `started_after`, `started_before`, `q`, `page`, `page_size`. Each has `parent_session_id` and `root_session_id` for delegation |
| `GET /sessions/{id}` | the session and its `operations[]`: `operation_type`, `timestamp`, `duration_seconds`, `success`, `error_message`, token counts, `tool_name`, `tool_use_id`, `tool_input`, `tool_output` |
| `GET /observability/sessions/{id}/tools` | `executions[]`: `operation_type`, `tool_name`, `timestamp`, `duration_ms`, `success`, `error_message`; param `limit` |
| `GET /observability/sessions/{id}/tokens` | `input_tokens`, `output_tokens`, `total_tokens`, `cache_creation_tokens`, `cache_read_tokens`, `total_cost_usd` |
| `GET /costs/sessions/{id}` | `total_cost_usd`, `cost_by_model`, `cost_by_tool`, `tokens_by_tool`, `unpriced_observation_count`, `unmeasured_fields` |
| `GET /costs/executions/{id}` | `total_cost_usd`, `cost_by_phase`, `unpriced_by_phase`, `cost_by_model`, `cost_by_tool`, `unpriced_observation_count`, `is_complete` |
| `GET /costs/sessions`, `GET /costs/executions`, `GET /costs/summary` | lists and the deployment-wide summary |
| `GET /metrics` | aggregated metrics; param `workflow_id` |
| `GET /insights/overview`, `/insights/cost`, `/insights/contribution-heatmap` | the `syn insights` views |

`unmeasured_fields` names fields that hold a default rather than a reading,
such as `compute_cost_usd`: report those as unknown, not zero.

Artifacts a session produced are read with `syn artifacts list -w
<workflow-id>`, `syn artifacts show <artifact-id>` and
`syn artifacts content <artifact-id>`.

Run `syn <group> <subcommand> --help` for the flags of the installed CLI
version.
