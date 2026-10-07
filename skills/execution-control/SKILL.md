---
name: execution-control
description: Use when handling a Syntropic137 workflow execution after it has started - checking its status and phases, following it live, cancelling or stopping it, resuming a failed, interrupted or cancelled run, or working out why it failed before deciding what to do next. This is the first stop for any "why did my run fail" question about an execution. Trigger phrases include "why did my run fail", "why did the workflow fail", "which phase failed", "check on my execution", "is the run done", "watch the execution", "cancel the run", "stop the execution", "resume the failed execution", "retry from the failed phase", "the run completed but nothing was pushed", "execution stuck", "run is queued", "cancel a queued run", "verification died on the PR", "syn execution", "syn control". Do NOT use for choosing or starting a workflow and its inputs (use syn-workflow), for steering a running agent with new instructions (not delivered as of 2026-10-03, see below), for session-level telemetry once the failing phase's session is known - its tool timeline, token and cache use, or what one session cost (use observing-sessions), or for patterns across many finished runs (use mining-session-logs).
---

# Controlling and diagnosing Syntropic137 executions

An execution is one run of a workflow: an `exec-...` id, a status, and one
entry per phase recording that phase's status, model, tokens, cost and
session.

Two mistakes dominate. The first is re-running a failed execution before
knowing which phase failed and why, which pays again for the same failure and
buries the evidence under a second run. The second is trusting a control
action because the API accepted it: an accepted request is not an effect, and
at least one control in this API is accepted and then does nothing. **Read
the execution before acting on it, and read it again after.**

## When to Use

- A run has started and you need its status, its phases, or to follow it live.
- You need to cancel, stop or resume an execution.
- Someone asks why a run, a workflow or an execution failed. Start here: the
  execution records which phase failed, how the platform classified the
  failure, and which session to read next.

## When NOT to Use

- You are choosing a workflow or starting a run: use syn-workflow.
- You already know the session and want its tool timeline, token and cache
  breakdown, or cost by model: use observing-sessions. Step 7 hands off there.
- You need every session of a run, including delegates: use
  discovering-run-sessions.
- You want patterns across many finished runs: use mining-session-logs.
- You want to steer a running agent with new instructions: nothing delivers
  that as of 2026-10-03 (see the anti-patterns).

## Input

- **Deployment** (required, environment): `SYN_API_URL`, default
  `http://localhost:8137`. Credentials are `SYN_API_TOKEN` (bearer) or
  `SYN_API_USER` + `SYN_API_PASSWORD` (basic). Check with `syn config show`
  and `syn health`.
- **Execution id** (string `exec-...`, required for every action except
  listing).
- **Status filter** (optional): `running`, `failed`, `completed`,
  `cancelled` or `interrupted`, for `syn execution list --status`.
- **Workflow id** (optional): to list one workflow's runs.
- **Cancel reason** (string, optional): `--reason`.
- **Resume overrides** (optional flags): `--override-cancellation`,
  `--acknowledge-external-effects`.

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

## Workflow

1. Check which deployment you are talking to with `syn config show` and
   `syn health`.

2. Find the execution:

   ```bash
   syn execution list
   syn execution list --status running      # or failed, completed, cancelled, interrupted
   syn workflow status <workflow-id>        # runs of one workflow
   ```

   `--page` and `--page-size` (at most 100) page through long lists.

3. Read it with `syn execution show <execution-id>`. This prints the status,
   start and completion times, total tokens and cost; the **Deliverable** and
   **Side effects** lines; the execution's error, if there is one; a
   **Resume start** block when this execution has been resumed; the
   repositories; a phases table (number, name, status marked `(recovered)`
   when the deliverable was salvaged, model, start time, tokens, cost, side
   effects), each failed phase's classification and error below the table;
   and a session inventory summary with its coverage. A phase's session id
   and artifact id are not shown; they are in the API response (step 7).

   An execution that was accepted but has not started shows a **Queue** line,
   for example `queued 2 of 3 (4/4 running)`: the deployment runs a fixed
   number of executions at once and this one is waiting for a slot. Read
   that line before concluding a run is lost or stuck, and do not start it
   again: the copy queues behind it.

4. Follow it live, if it is running:

   ```bash
   syn watch execution <execution-id>       # streams events until you stop it
   syn watch activity                       # everything running on the deployment
   ```

   For a periodic check without streaming, re-run `syn execution show`. A
   running execution's cost and token totals grow as phases report.

5. Cancel or stop it, if it should not continue:

   ```bash
   syn control cancel <execution-id> --force --reason "wrong repository"
   syn control stop <execution-id> --force          # the same cancel, default reason
   syn control status <execution-id>                # id and state only
   ```

   Both refuse without `--force`, a deliberate pause to check the id. What
   a cancel does depends on where the execution is:

   - **queued, not yet started:** the start is withdrawn and the run never
     begins;
   - **running:** the cancellation is queued and the agent is interrupted as
     its output is processed, so it is not instantaneous.

   The CLI prints "Cancel signal sent" in both cases; only its `Message:`
   line says which happened. Judge the outcome with `syn execution show`,
   not the cancel response: re-read until the status is `cancelled` or the
   Queue line is gone.

6. Read what the run delivered, whatever its status. `completed` and
   `failed` describe the harness: the phases ended, or one did not. They do
   not say whether the work is right. Read the last phase's reported result
   (its artifact, step 7, item 5) and the pull request or other output it
   names. A phase that refused a false premise, or reported that it delivered part
   of the task and named the rest, did its job; count that as a correct
   outcome, not a failure to retry.

7. If it failed, diagnose it before acting. Work down this list and stop when
   the cause is clear:
   1. **The execution's outcome.** In `syn execution show`: the error, the
      Deliverable and Side effects lines, and which phase is `failed`.
   2. **How the platform classified it.** Fetch
      `GET $SYN_API_URL/api/v1/executions/<execution-id>` and read
      `failure_classification`, `reported_failure_reason`,
      `reported_side_effects`, `deliverable_produced`, `error_message` and the
      failing phase's `error_message` and `session_id`. What each field and
      value means is in
      [references/diagnosis-fields.md](references/diagnosis-fields.md).
   3. **What the agent did.** With the failing phase's session id:
      `syn sessions show <session-id>` (operations in order, success flags,
      error), `syn observe tools <session-id>` (tool timeline, durations, ok
      or error) and `syn observe tokens <session-id>` (token breakdown). An
      operation of type `tool_blocked` in `syn sessions show` means a tool
      call was refused by policy, which usually explains a `denied`
      write-back. `syn sessions list --execution <execution-id>` lists the
      execution's sessions, with ids shortened to eight characters. Deeper
      session telemetry belongs to observing-sessions.
   4. **Every session the execution started**, including subagents and nested
      runs, with gaps in capture made explicit:
      `syn execution sessions <execution-id> --all`, or
      `syn execution sessions <execution-id> --phase <phase-id> --json`.
   5. **The output.** `syn artifacts show <artifact-id>` or
      `syn artifacts content <artifact-id>`.

8. Decide from what step 7 found:

   | finding | do |
   |---|---|
   | `platform` failure, the phase never really ran | resume |
   | `task` failure: wrong instructions, a wrong premise, scope too large for one phase, missing input | fix the task or inputs and start a new run with syn-workflow; resume replays the same task text and fails the same way |
   | `correct_refusal` or `refused` | the agent was right to stop; change what was asked, not how often |
   | `reported_side_effects` is `denied` | read the actual refusal first (the phase error and session): `denied` also covers a protected branch or a read-only token, not only a missing App permission. Fix that cause, then resume with `--acknowledge-external-effects` if the phase must run again |
   | deliverable produced, status failed | read the artifact before re-running anything |
   | the implementation pushed a pull request, then the verification phase died | start a workflow whose only phase verifies an existing pull request, pointed at that PR, rather than resuming a run that would implement again |
   | cause still unclear | report the execution id, the failing phase, its error, and its session id to the deployment's operator rather than retrying |

9. Resume it, if step 8 says so. Resuming keeps the phases that already
   completed; a fresh `syn workflow run` pays for them again:

   ```bash
   syn execution resume <execution-id>
   syn execution resume <execution-id> --acknowledge-external-effects
   syn execution resume <execution-id> --override-cancellation
   ```

   | execution status | resumable |
   |---|---|
   | `failed`, `interrupted` | yes |
   | `cancelled` | only with `--override-cancellation` |
   | `completed` | no, nothing is left to run |
   | `running`, `not_started` | no |
   | already resumed once | no, the error names the execution it was resumed as; resume that one |

   The new execution inherits the **unbroken run of completed phases from the
   start** and re-runs from the first phase after it. A phase that completed
   after a failed one is not inherited and runs again. If the phase being
   resumed ever started, it may already have pushed, commented or published,
   and re-running it may do so twice; the API then requires
   `--acknowledge-external-effects`. Check the failed phase's side effects
   (step 3) before you pass it.

10. Confirm the resume. On success the CLI prints the parent, the **new
    execution id**, the phase it resumes at, and the phases not re-run. The
    resume is accepted before the new execution starts. Read the **parent**
    with `syn execution show` to see its `Resume start` block: its status
    (`pending`, `paused`, `retryable`, `dispatched`, `started` or `failed`),
    attempts against the maximum, and a reason when the start has stalled or
    failed. Then follow the new execution from step 3. If it also fails,
    resume the new execution, not the original.

## Output

- The execution's recorded state: status, failing phase and its error,
  Deliverable and Side effects, reported to the caller.
- For a failure: a named attribution (task, platform, correct refusal, or a
  missing permission) and the decision taken from the table in step 8, with
  the evidence that made it.
- After a cancel: the execution read back as `cancelled`.
- After a resume: the new execution id, and its `Resume start` status read
  from the parent.

## Outcomes we are looking for

### Outcome 1: every action is based on the execution's recorded state

- *Signal:* before cancelling, resuming or re-running, the caller has the
  execution's status, its failing phase, and that phase's error.
- *Signal:* the decision to resume, re-run, or fix something else first is
  stated with the evidence that made it.

### Outcome 2: every control action is confirmed by its effect

- *Signal:* after a cancel, the execution is read again until it shows
  `cancelled` (or, for a queued run, its Queue line is gone), rather than
  reported cancelled on the strength of the response.
- *Signal:* after a resume, the new execution id is reported and its start is
  checked.

### Outcome 3: a failure is attributed before it is retried

- *Signal:* the failure is named as one of: the task itself, the platform, a
  correct refusal, or a permission the run did not have.
- *Signal:* a run whose write-back was denied is answered by granting the
  permission, not by running the same thing again.
- *Signal:* a refused premise or a reported partial delivery is recorded as
  the agent behaving correctly, and the next run carries a changed task.

## Anti-patterns

- **Re-running blind.** Starting the workflow again without reading the failed
  phase's error.
- **Re-dispatching a queued run.** An execution with a Queue line in
  `syn execution show` is waiting for a slot, not lost. Starting it again
  adds a second copy behind it in the same queue.
- **Reading the cancel response as the outcome.** It says "Cancel signal
  sent" whether the run was withdrawn from the queue or is still being
  interrupted.
- **Reading `completed` as "the work is right" or `failed` as "the work is
  missing".** On runs observed 2026-10-04..06, an agent refusing a false
  premise and a run dying in verification after its pull request was open
  both looked wrong by status alone. The phase's reported result and the PR
  are the outcome.
- **Resuming a task failure.** A resume replays the same task text, so a
  task too large for one phase, or built on a wrong premise, fails the same
  way again.
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

## Recommended tools and practices (as of 2026-10-07)

### Outcome: every action is based on the execution's recorded state

- **`syn execution show` as the first read.** Ladders up by putting status,
  Deliverable, Side effects and the phases on one screen. Tradeoffs: it omits
  phase errors, session ids and artifact ids.
- **`GET /executions/{id}` for what `show` omits.** Ladders up by exposing
  the per-phase error, session and artifact ids that step 7 needs. The full
  route list is in [references/http-api.md](references/http-api.md).
- **The Queue line before any "is it lost" conclusion.** Ladders up by
  showing a run accepted but waiting for a slot, with its position and how
  many are running. Tradeoffs: none.
- **The last phase's reported result and the PR over the status.** Ladders
  up because the status describes the harness and the result describes the
  work. Tradeoffs: one more read per run.

### Outcome: every control action is confirmed by its effect

- **Read, act, read again with `syn execution show`.** Ladders up by turning
  an accepted request into an observed effect. Tradeoffs: cancellation is
  not instantaneous, so the re-read may need repeating.
- **The parent's `Resume start` block.** Ladders up because the resume is
  accepted before the new execution starts, and this block is where a stalled
  or failed start shows, including its own Queue line.

### Outcome: a failure is attributed before it is retried

- **`failure_classification` beside `reported_failure_reason`.** Ladders up
  by giving the platform's attribution and the agent's own, so a disagreement
  between them is visible. See
  [references/diagnosis-fields.md](references/diagnosis-fields.md).
- **`syn sessions show` for `tool_blocked` operations.** Ladders up by
  locating the policy refusal behind a `denied` write-back.
- **Resume for platform failures, a new run for task failures, a
  verify-only run for a dead verification.** Ladders up by paying only for
  the phase that needs to run again. Tradeoffs: a verify-only workflow must
  be registered on the deployment (see syn-workflow).

Run `syn execution <subcommand> --help` and `syn control <subcommand> --help`
for the flags of the installed CLI version.

## References

- [references/diagnosis-fields.md](references/diagnosis-fields.md): every
  field of the execution detail used to attribute a failure, with its values.
  Read during step 7.
- [references/http-api.md](references/http-api.md): the HTTP routes behind
  the CLI, including cancel and resume bodies and the `inject` caveat. Read
  when you need structured output or the CLI is unavailable.

## Continual improvement

File drift, gaps, or proposed updates at
https://github.com/syntropic137/syntropic137-skills/issues
