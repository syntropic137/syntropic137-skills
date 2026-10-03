---
name: execution-control
description: Use when handling a Syntropic137 workflow execution after it has started - checking its status and phases, following it live, cancelling or stopping it, resuming a failed, interrupted or cancelled run, or working out why it failed before deciding what to do next. Trigger phrases include "check on my execution", "is the run done", "watch the execution", "cancel the run", "stop the execution", "resume the failed execution", "retry from the failed phase", "why did the workflow fail", "which phase failed", "the run completed but nothing was pushed", "execution stuck", "syn execution", "syn control". Do NOT use for choosing or starting a workflow and its inputs (use syn-workflow), for steering a running agent with new instructions (not delivered as of 2026-10-03, see below), or for patterns across many finished runs (use mining-session-logs).
---

# Controlling and diagnosing Syntropic137 executions

An execution is one run of a workflow: an `exec-...` id, a status, and one
entry per phase recording that phase's status, model, tokens, cost and
session. This skill covers everything after the run starts: watching it,
stopping it, resuming it, and finding out why it failed.

Two mistakes dominate. The first is re-running a failed execution before
knowing which phase failed and why, which pays again for the same failure and
buries the evidence under a second run. The second is trusting a control
action because the API accepted it: an accepted request is not an effect, and
at least one control in this API is accepted and then does nothing. **Read
the execution before acting on it, and read it again after.**

## Outcomes we are looking for

### Outcome 1: every action is based on the execution's recorded state

- *Signal:* before cancelling, resuming or re-running, the caller has the
  execution's status, its failing phase, and that phase's error.
- *Signal:* the decision to resume, re-run, or fix something else first is
  stated with the evidence that made it.

### Outcome 2: every control action is confirmed by its effect

- *Signal:* after a cancel, the execution is read again until it shows
  `cancelled`, rather than reported cancelled on the strength of the response.
- *Signal:* after a resume, the new execution id is reported and its start is
  checked.

### Outcome 3: a failure is attributed before it is retried

- *Signal:* the failure is named as one of: the task itself, the platform, a
  correct refusal, or a permission the run did not have.
- *Signal:* a run whose write-back was denied is answered by granting the
  permission, not by running the same thing again.

## Before you start

Every command talks to one deployment. Check which one:

```bash
syn config show     # SYN_API_URL and whether credentials are set
syn health
```

`SYN_API_URL` defaults to `http://localhost:8137`. Credentials are
`SYN_API_TOKEN` (bearer) or `SYN_API_USER` + `SYN_API_PASSWORD` (basic).

## The state model

```
not_started -> running -> completed
                       -> failed       --+
                       -> interrupted  --+-- resume -> a NEW execution that
                       -> cancelled    --+   inherits the completed phases
                                             (cancelled needs an override)
```

There is no `paused` state and no pause command. Phases move through
`pending`, `running`, then `completed`, `failed` or `skipped`.

Status alone does not tell you whether the work landed. `syn execution show`
reports two outcome lines beside it:

- **Deliverable:** whether the run produced its deliverable. A run can fail
  after its deliverable exists.
- **Side effects:** what the agent reported about its write-back: `none`,
  `succeeded`, `denied`, or `failed`. A run can complete while its push was
  refused.

## Principles

- **Read, act, read again.** Each control action is followed by
  `syn execution show` until the state you expected is there.
- **Destructive actions need `--force`.** `syn control cancel` and
  `syn control stop` refuse without it. That is a deliberate pause for you to
  check the id, not an obstacle.
- **Resume, don't restart.** Resuming keeps the phases that already
  completed; a fresh `syn workflow run` pays for them again.
- **One resume per execution.** If the resumed run also fails, resume the new
  execution, not the original.

## Anti-patterns

- **Re-running blind.** Starting the workflow again without reading the failed
  phase's error.
- **Steering with `inject`.** `syn control inject` returns success and queues
  the message, but as of 2026-10-03 nothing delivers it to the running agent.
  The agent never sees it. To change what a run does, cancel it and start it
  again with a corrected task.
- **Reading `syn control status` for progress.** It prints only the
  execution id and its state. Phases, errors, cost and sessions are in
  `syn execution show`.
- **Passing an execution id to `syn workflow status`.** That takes a
  workflow id and lists its runs.
- **Retrying a `denied` write-back.** The run did its work and was refused
  permission to publish it. Running again is refused again.
- **Looking for a budget cap.** There is no per-execution spend limit flag. A
  `max_budget_usd` field may still appear in old examples of the execute
  request; it is ignored.

## The procedure

### 1. Find the execution

```bash
syn execution list
syn execution list --status running      # or failed, completed, cancelled, interrupted
syn workflow status <workflow-id>        # runs of one workflow
```

`--page` and `--page-size` (at most 100) page through long lists.

### 2. Read it

```bash
syn execution show <execution-id>
```

This prints:

- Status, start and completion times, total tokens and cost.
- The **Deliverable** and **Side effects** lines.
- The execution's error, if there is one.
- A **Resume start** block when this execution has been resumed.
- The repositories.
- A phases table: number, name, status (marked `(recovered)` when the
  deliverable was salvaged), model, start time, tokens, cost, side effects.
- A session inventory summary and its coverage.

The phases table does **not** show a phase's error message, its session id,
or its artifact id. Those are in the API response (step 6).

### 3. Follow it live

```bash
syn watch execution <execution-id>       # streams events until you stop it
syn watch activity                       # everything running on the deployment
```

For a periodic check without streaming, re-run `syn execution show`. A
running execution's cost and token totals grow as phases report.

### 4. Cancel or stop it

```bash
syn control cancel <execution-id> --force --reason "wrong repository"
syn control stop <execution-id> --force          # the same cancel, default reason
syn control status <execution-id>                # id and state only
```

Cancel is accepted only while the execution is `running`. Acceptance queues
the cancellation; the running agent is interrupted as its output is
processed, so it is not instantaneous. Confirm with `syn execution show`
until the status is `cancelled`.

### 5. Resume it

```bash
syn execution resume <execution-id>
syn execution resume <execution-id> --acknowledge-external-effects
syn execution resume <execution-id> --override-cancellation
```

What the API enforces:

| execution status | resumable |
|---|---|
| `failed`, `interrupted` | yes |
| `cancelled` | only with `--override-cancellation` |
| `completed` | no, nothing is left to run |
| `running`, `not_started` | no |
| already resumed once | no, the error names the execution it was resumed as; resume that one |

The new execution inherits the **unbroken run of completed phases from the
start** and re-runs from the first phase after it. A phase that completed
after a failed one is not inherited and runs again.

If the phase being resumed ever started, it may already have pushed,
commented or published, and re-running it may do so twice. The API then
requires `--acknowledge-external-effects`. Check the failed phase's side
effects (step 2) before you pass it.

On success the CLI prints the parent, the **new execution id**, the phase it
resumes at, and the phases not re-run. The resume is accepted before the new
execution starts. Read the **parent** with `syn execution show` to see its
`Resume start` block: its status (`pending`, `paused`, `retryable`,
`dispatched`, `started` or `failed`), attempts against the maximum, and a
reason when the start has stalled or failed. Then follow the new execution.

### 6. Diagnose a failure

Work down this list and stop when the cause is clear.

1. **The execution's outcome.** In `syn execution show`: the error, the
   Deliverable and Side effects lines, and which phase is `failed`.
2. **How the platform classified it.** From the API:

   ```bash
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

3. **What the agent did.** With the failing phase's session id:

   ```bash
   syn sessions show <session-id>       # operations in order, success flags, error
   syn observe tools <session-id>       # tool timeline, durations, ok or error
   syn observe tokens <session-id>      # token breakdown
   ```

   An operation of type `tool_blocked` in `syn sessions show` means a tool
   call was refused by policy, which usually explains a `denied` write-back.
   `syn sessions list --execution <execution-id>` lists the execution's
   sessions, with ids shortened to eight characters.

4. **Every session the execution started**, including subagents and nested
   runs, with gaps in capture made explicit:

   ```bash
   syn execution sessions <execution-id> --all
   syn execution sessions <execution-id> --phase <phase-id> --json
   ```

5. **The output.** `syn artifacts show <artifact-id>` or
   `syn artifacts content <artifact-id>`.

Then decide:

| finding | do |
|---|---|
| `platform` failure, the phase never really ran | resume |
| `task` failure: wrong instructions, missing input, the agent could not do it | fix the task or inputs and start a new run with syn-workflow; resume repeats the same instructions |
| `correct_refusal` or `refused` | the agent was right to stop; change what was asked, not how often |
| `reported_side_effects` is `denied` | read the actual refusal first (the phase error and session): `denied` also covers a protected branch or a read-only token, not only a missing App permission. Fix that cause, then resume with `--acknowledge-external-effects` if the phase must run again |
| deliverable produced, status failed | read the artifact before re-running anything |
| cause still unclear | report the execution id, the failing phase, its error, and its session id to the deployment's operator rather than retrying |

## Recommended tools and practices (as of 2026-10-03)

All of the above is also plain HTTP against `$SYN_API_URL/api/v1`. Send the
`Authorization` header that matches your credentials:

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
API="$SYN_API_URL/api/v1"
curl -sf -H "$AUTH" "$API/executions?status=running&page=1&page_size=50"
curl -sf -H "$AUTH" "$API/executions/<execution-id>"
curl -sf -H "$AUTH" "$API/executions/<execution-id>/state"
curl -sf -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$API/executions/<execution-id>/cancel" -d '{"reason": "wrong repository"}'
curl -sf -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$API/executions/<execution-id>/resume" \
  -d '{"override_cancellation": false, "acknowledge_external_effects": true}'
```

| endpoint | returns |
|---|---|
| `GET /executions` | a page of executions; params `status`, `statuses`, `page`, `page_size` |
| `GET /executions/{id}` | the full detail described in step 6 |
| `GET /executions/{id}/state` | `execution_id` and `state` only |
| `GET /executions/{id}/session-inventory` | the session inventory behind `syn execution sessions` |
| `GET /workflows/executions/active` | executions currently active |
| `POST /executions/{id}/cancel` | `success`, `execution_id`, `state`, `message`, `error` |
| `POST /executions/{id}/resume` | `parent_execution_id`, `execution_id`, `resume_phase_id`, `inherited_phase_ids`, `cancellation_overridden`, `external_effects_acknowledged` |

There is no `/executions/{id}/status` route; use `/state` for the bare state
or the detail route for everything else.

`POST /executions/{id}/inject` and `syn control inject` exist and answer
success, but the message is not delivered to the running agent as of this
date. Do not use them to steer a run, and do not report a run as steered
because inject returned success.

Run `syn execution <subcommand> --help` and `syn control <subcommand> --help`
for the flags of the installed CLI version.
