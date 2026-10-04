---
name: observing-sessions
description: Use when working out what a Syntropic137 agent session did, why it cost what it cost, or why one known session failed - its operations log, tool timeline, token and cache breakdown, cost by model, tool and phase, and platform-wide cost and activity. Trigger phrases include "why was this run expensive", "why did this session cost so much", "what did the agent do", "what did the agent do in this phase", "show the tool calls", "token usage of this session", "cache hit rate", "cost breakdown", "which phase cost the most", "why did this session fail", "cost shows unpriced", "syn sessions", "syn observe", "syn costs", "syn metrics", "syn insights". Do NOT use as the first stop for "why did my run fail" or "why did the workflow or execution fail": the execution's failing phase, failure classification, cancel and resume belong to execution-control, which hands over here once the failing session is known. Do NOT use for listing every session of a run including delegates and native transcripts (use discovering-run-sessions), or for lessons across many finished runs (use mining-session-logs).
---

# Observing Syntropic137 sessions and costs

A session is one headless agent invocation in one workspace: `claude -p` or
`codex exec`, depending on the harness the phase declared. A three-phase
workflow run starts three platform sessions, and phases of one run can use
different harnesses.

Two mistakes dominate. The first is answering "why was it expensive" from the
total alone, when the breakdowns that explain it (by phase, by model, by tool,
cached versus uncached) are one command away. The second is reading a cost of
`$0` or a short total as cheap work, when it can mean the platform had no rate
for the model that ran. **A cost is a reading with a coverage, and the
coverage is part of the answer.**

## When to Use

- You want to know why a run or a session cost what it did, broken down by
  phase, model, tool and cache.
- You want to know what an agent did in a session or a phase: its operations,
  tool calls and timing.
- You already have the failing session (from execution-control, or given to
  you) and need to explain the failure from its record.
- A cost shows `unpriced` or `(partial)`.
- You want deployment-wide cost and activity.

## When NOT to Use

- Someone asks why a run, workflow or execution failed and the failing phase
  is not yet known: start with execution-control. It reads the execution's
  failure classification and names the session to bring here.
- You need to cancel or resume an execution: use execution-control.
- You need every session of a run, including delegates and native
  transcripts: use discovering-run-sessions.
- You want lessons across many finished runs: use mining-session-logs.

## Input

- **Deployment** (required, environment): `SYN_API_URL`, default
  `http://localhost:8137`. Credentials are `SYN_API_TOKEN` (bearer) or
  `SYN_API_USER` + `SYN_API_PASSWORD` (basic). Check with `syn config show`
  and `syn health`.
- **Execution id** (`exec-...`) or **session id** (one of them required). If
  you only have a workflow, list its runs with
  `syn workflow status <workflow-id>`, or use execution-control to find the
  execution.
- **Workflow id** (optional): scopes `syn metrics show -w` and
  `syn sessions list -w`.
- **Session list filters** (optional): `--execution <id>`, `-w/--workflow
  <id>`, `-s/--status <status>` (`running`, `completed`, `failed`,
  `cancelled`), `-n/--limit`.

## Workflow

1. Check which deployment you are talking to with `syn config show` and
   `syn health`.

2. Pick the view that answers the question. The full table of views, and
   what each one shows, is in
   [references/views.md](references/views.md):
   - cost of a run: `syn costs execution <execution-id>`;
   - cost of a session: `syn costs session <session-id>`;
   - what a session did: `syn sessions show <session-id>`;
   - tools in order with durations: `syn observe tools <session-id>`;
   - tokens and cache: `syn observe tokens <session-id>`.

3. For "why was this run expensive", run `syn costs execution <execution-id>`
   and read, in order:
   1. **Coverage.** If the cost is `unpriced` or `(partial)`, say so first.
      The API's `unpriced_by_phase` names the phases whose cost is unknown: a
      phase listed there and absent from `cost_by_phase` cost an unknown
      amount.
   2. **Cost by phase.** The phase that carries the cost.
   3. **Cost by model.** A top-tier model doing shallow work is the most
      common avoidable cost.
   4. **Cost by tool.** Which tools the money went through.

4. Narrow to the expensive phase's session. Take its id from
   `syn sessions list --execution <execution-id>`, or `phases[].session_id`
   in `GET /executions/{id}`, and run `syn costs session <session-id>` and
   `syn observe tokens <session-id>`. High cache read tokens relative to
   cache creation means the session reused its context. Low cache reads
   beside high input tokens means it reloaded context on many turns: large
   file reads or long command output repeated across turns. The session
   cost's `tokens_by_tool` (API only) shows which tools the tokens were
   attributed to; it is an estimate.

5. For "what did this session do", run `syn sessions show <session-id>` and
   `syn observe tools <session-id>` (`--limit`, default 100). The operations
   log is the whole record: messages, tool starts and completions, blocked
   tools, thinking, errors. The tool timeline is the same tool calls with
   timing, for finding the slow step. The timeline has no inputs or outputs;
   for those, read the session's operations over the API
   (`GET /sessions/{id}`), where each carries `tool_name`, `tool_use_id`,
   `tool_input` and `tool_output`. `tool_input` and `tool_output` are
   previews cut to 500 characters, not the full payload, so a long command or
   file body is truncated there.

6. For "why did this session fail":
   1. `syn sessions show <session-id>`: the `Error:` line, then the last
      operations before it. Look for operations that did not succeed and for
      `tool_blocked`.
   2. `syn observe tools <session-id>`: tools that ended in `error`, and
      durations that point to a hang.
   3. The tool's own input and output previews, from the operations over the
      API.
   4. The phase's error and the execution's failure classification: use
      execution-control.

7. For "why does the cost say unpriced": the platform records no dollar
   figure for work on a model it has no rate for, rather than a wrong one. On
   codex phases this happens when the phase names a model the platform does
   not price; a codex phase that left its model unset is given the
   platform's default codex model when the workflow is installed, and is
   priced as that. Codex itself reports no vendor cost, so the platform's
   figure is computed from tokens. Report the token counts, the unpriced
   observation count, and the model the session reported
   (`syn sessions show`, `Model:`).

## Output

- A cost answer that names the phase, the model and the tools that carried
  the cost, each with its figure, and the cache read and cache write counts.
- The cost's coverage, stated beside the number: `unpriced` or
  `>=$X (partial)` with the unpriced observation count, and any
  `unmeasured_fields` reported as unknown.
- For a failure: the operation where the session went wrong, its type and its
  error message.
- Nothing is changed on the deployment; every command here is a read.

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

## Anti-patterns

- **Treating `$0` as free.** When observations had no rate for their model,
  the CLI shows `unpriced` (nothing could be priced) or `>=$X (partial)` (a
  lower bound). Tokens are still counted.
- **Looking for blocked tools in `syn observe tools`.** It shows ok or error.
  A blocked call is an operation of type `tool_blocked` in
  `syn sessions show`.
- **Passing a workflow id to `syn costs execution`.** It takes an execution
  id.
- **Counting a run's agents with `syn sessions list`.** It shows
  **platform** sessions only. Delegates an agent starts inside its workspace
  and the harness's own transcripts are not in it; use
  discovering-run-sessions.
- **Comparing models by alias.** `cost_by_model` is keyed by the model id the
  harness reported. Cost whose model no harness reported is under
  `unattributed-model`.
- **Reading a sparse codex timeline as a failure.** Hook events, subagent
  tracking and TodoWrite are recorded for claude sessions only. A codex
  session's record is thinner by construction: its tool timeline is mapped
  from codex events (`command_execution` appears as `Bash`, `file_change` as
  `Edit`).
- **Quoting a tool preview as the whole input.** `tool_input` and
  `tool_output` stop at 500 characters.

## Recommended tools and practices (as of 2026-10-04)

### Outcome: every cost claim names where the cost went

- **`syn costs execution` first, then the expensive phase's session.**
  Ladders up by starting from cost by phase and narrowing to the session
  that carries it. Tradeoffs: takes an execution id, not a workflow id.
- **`syn observe tokens` for cache.** Ladders up by giving cache creation and
  cache read counts to state cache behaviour from. **`tokens_by_tool`** from
  `GET /costs/sessions/{id}` attributes tokens to tools. Tradeoffs: an
  estimate, API only.
- **`syn metrics show` and `syn insights`** for workflow-wide and
  deployment-wide totals. Ladders up when the question spans many runs.

### Outcome: incomplete costs are reported as incomplete

- **Quote the CLI's `unpriced` or `(partial)` marker and the unpriced
  observation count every time.** Ladders up by keeping coverage attached to
  the number it qualifies.
- **`unpriced_by_phase` and `unmeasured_fields` from the cost API.** Ladders
  up by naming which phases and which fields hold no reading. Fields such as
  `compute_cost_usd` listed in `unmeasured_fields` are unknown, not zero.

### Outcome: a failure is explained from the session's own record

- **`syn sessions show` for the operations log.** Ladders up because it is
  the one view that shows `tool_blocked` and the session's `Error:` line.
- **`GET /sessions/{id}` for tool input and output previews.** Ladders up by
  showing what a failing tool was called with. Tradeoffs: previews are cut
  to 500 characters.

Every endpoint, with its parameters and fields, is in
[references/http-api.md](references/http-api.md). Run
`syn <group> <subcommand> --help` for the flags of the installed CLI version.

## References

- [references/views.md](references/views.md): every CLI view, the question it
  answers and what it shows, plus the artifact commands. Read when step 2's
  short list does not cover the question.
- [references/http-api.md](references/http-api.md): the sessions,
  observability, costs, metrics and insights routes with their fields. Read
  when you need structured output, tool input and output previews, or the
  CLI is unavailable.

## Continual improvement

File drift, gaps, or proposed updates at
https://github.com/syntropic137/syntropic137-skills/issues
