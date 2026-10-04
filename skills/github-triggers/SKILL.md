---
name: github-triggers
description: Use when making a Syntropic137 workflow run automatically on GitHub events, or managing the trigger rules that do so - registering a rule or enabling a built-in preset, choosing its event, conditions, input mapping and safety limits, pausing, resuming or deleting rules, and working out why a trigger did or did not fire. Trigger phrases include "run this workflow on every PR", "set up a trigger on PR merge", "auto-fix failing CI", "self-healing", "respond to review comments", "/syn comment command", "set up a trigger", "why didn't my trigger fire", "trigger fired too often", "pause the trigger", "stop all triggers on this repo", "trigger history", "syn triggers". Do NOT use for starting a workflow by hand (use syn-workflow), for following or cancelling the executions a trigger started (use execution-control), or for installing the GitHub App or exposing a webhook URL, which is deployment setup rather than product use.
---

# Running Syntropic137 workflows from GitHub events

A trigger rule is a standing instruction: *when event E happens on repository
R and the payload matches conditions C, start workflow W with inputs taken
from the payload, unless a safety guard says no.* Each decision, fired or
blocked, is recorded in the rule's history with the guard and reason.

Two mistakes dominate. The first is a rule that never fires because its
event is spelled the way GitHub names the webhook (`pull_request`) when the
platform matches the event **and its action** (`pull_request.opened`). The
second is a rule that fires and does nothing useful because no input mapping
told the workflow which repository and pull request it was for. **Read the
rule's history before changing it, and check that a fired run received the
inputs it needed.**

## When to Use

- You want a workflow to run on a GitHub event: a pull request opened or
  merged, a failing check, a review, a `/syn` comment.
- You want to enable a built-in preset (`self-healing`, `review-fix`,
  `comment-command`).
- A trigger did not fire, fired too often, or fired and did nothing.
- You need to pause, resume or delete trigger rules.

## When NOT to Use

- You want to start a workflow by hand: use syn-workflow.
- You want to follow, cancel or diagnose the execution a trigger started:
  use execution-control.
- You need to install the GitHub App or expose a webhook URL: that is
  deployment setup, not product use.

## Input

- **Deployment** (required, environment): `SYN_API_URL`, default
  `http://localhost:8137`. Credentials are `SYN_API_TOKEN` (bearer) or
  `SYN_API_USER` + `SYN_API_PASSWORD` (basic). Check with `syn config show`
  and `syn health`. Name it: the workflow id only resolves there.
- **Repository** (`owner/repo`, required): the deployment's GitHub App must be
  installed on it; `syn github repos` lists the repositories it can reach.
- **Workflow id** (required for a rule; optional for a preset): it must be
  registered, `syn workflow list` (see syn-workflow).
- **Event** (required for a rule): `<event>.<action>`, or the bare event name
  when GitHub sends no action.
- **Conditions** (optional): payload path, operator, value.
- **Input mapping** (optional, API only): workflow input name to payload
  path.
- **Limits** (optional): `max_attempts`, `daily_limit`, `cooldown_seconds`.
- **Trigger id** (string, required for show, history, pause, resume, delete).

## How a rule decides

1. **Event and repository.** The incoming event is `<event>.<action>` when
   GitHub sends an action (`pull_request.opened`, `check_run.completed`,
   `issue_comment.created`) and the bare event name when it does not
   (`push`). The repository is `owner/repo`. Both must equal the rule's,
   exactly. A rule with event `pull_request` never matches an opened pull
   request.
2. **Conditions.** Every condition must hold. A condition is a dot-notation
   path into the payload, an operator, and a value. Operators: `eq`, `neq`,
   `in`, `not_in`, `contains`, `not_empty`, `is_empty`. Over the API a value
   is a string: `"false"` and `"true"` compare as booleans, and `in` and
   `not_in` take a comma-separated list. A miss is recorded as blocked by
   `conditions_not_met`.
3. **Safety guards**, each recorded by name when it blocks: `max_attempts`,
   `cooldown`, `daily_limit`, `idempotency`, `concurrency` and
   `dispatch_rate_limit`. What each one blocks is in
   [references/guards-and-presets.md](references/guards-and-presets.md). A
   blocked event is not retried later. Different rules do not block each
   other on the same pull request.
4. **Input mapping.** Each workflow input is read from a payload path, for
   example `"pr_number": "pull_request.number"`. A path that resolves to
   nothing is left out. An input named `repository` holding `owner/repo`
   also becomes the repository the run checks out.

## Workflow

1. Check the deployment (`syn config show`, `syn health`), that the App
   reaches the repository (`syn github repos`), and that the workflow is
   registered (`syn workflow list`).

2. Prefer a preset when one fits, because presets carry a tested event,
   conditions, input mapping and limits:

   ```bash
   syn triggers enable self-healing -r owner/repo [-w <workflow-id>]
   ```

   The three presets, their events and mapped inputs are in
   [references/guards-and-presets.md](references/guards-and-presets.md).
   Without `-w`, a preset dispatches the deployment's `self-heal-pr`
   workflow. Enabling the same preset twice on a repository is refused.

3. Otherwise register a rule. The CLI registers the simple case:

   ```bash
   syn triggers register -r owner/repo -w <workflow-id> -e pull_request.opened \
     -c pull_request.base.ref=main --max-attempts 3 --cooldown 300
   ```

   `-c field=value` repeats, and each is an `eq` condition. `--max-attempts`
   defaults to 5 and `--cooldown` to 300 seconds. The CLI sends no input
   mapping, a `daily_limit` of 20 and a generated name. With input mapping,
   other operators, a name or a different daily limit, use `POST /triggers`;
   a complete request body is in
   [references/http-api.md](references/http-api.md).

4. Read the rule back:

   ```bash
   syn triggers show <trigger-id>
   syn triggers list -r owner/repo        # -s active|paused|deleted, -a includes deleted
   ```

5. If it did not fire, read `syn triggers history <trigger-id>` (`-n`,
   default 20):
   - **A `blocked` entry** names the guard and the reason.
     `conditions_not_met` means the payload did not match: compare the
     conditions in `syn triggers show` with the event's payload.
   - **No entry at all** means no event reached this rule. Check the rule's
     event spelling (`<event>.<action>`), its repository (`owner/repo`),
     that it is `active`, and whether its event arrives without webhooks
     (see the anti-patterns).

6. If it fired and did nothing, the history's execution id is the run. Read
   it with execution-control. Then read its `inputs` (`GET /executions/{id}`)
   against the inputs the workflow needs: a missing input is a missing or
   wrong `input_mapping` path.

7. To stop a rule, pause before you delete, because pausing keeps the rule
   and its history:

   ```bash
   syn triggers pause <trigger-id>
   syn triggers resume <trigger-id>
   syn triggers disable-all -r owner/repo --force   # pauses every active rule on the repository
   syn triggers delete <trigger-id> --force         # soft delete; no command restores it
   ```

   `delete` and `disable-all` refuse without `--force`. `disable-all` pauses;
   resume rules one by one. `delete` is a soft delete: the rule's status
   becomes `deleted` and it stays listed with `syn triggers list -s deleted`
   or `-a`, but it never fires again and there is no command or route that
   restores it. To run the same thing again, register a new rule.

## Output

- A registered or enabled rule, read back with `syn triggers show`, with its
  event, repository, conditions, input mapping and limits stated, and the
  deployment named.
- For a non-fire: the history entry's guard and reason, or the absence of
  any entry and which of event, repository, status or delivery explains it.
- For a fire that did nothing: the execution id and the input that was
  missing from its `inputs`.
- For a stopped rule: its status `paused` or `deleted`.

## Outcomes we are looking for

### Outcome 1: every rule is armed deliberately

- *Signal:* the rule's event, repository, conditions, input mapping and
  limits are stated before it is registered, and read back with
  `syn triggers show` after.
- *Signal:* the deployment the rule was registered on is named, because the
  workflow id only resolves there.

### Outcome 2: a fire or a non-fire is explained from the history

- *Signal:* "it didn't fire" is answered with the history entry's guard and
  reason, or with the absence of any entry, which points at event delivery or
  at the event and repository the rule matches.

### Outcome 3: a noisy rule is disarmed, not deleted, while it is understood

- *Signal:* a rule firing too often is paused, its history is read, and only
  then is it changed or deleted.

## Anti-patterns

- **The bare event name for an event with actions.** Register
  `pull_request.opened`, not `pull_request` with a condition `action=opened`.
- **A rule with no input mapping for a workflow that needs inputs.** It fires,
  and the run starts with no inputs and no repository.
- **Assuming every event arrives.** Without a reachable webhook URL the
  platform learns of events by polling GitHub. `push`, `pull_request`,
  `pull_request_review`, `pull_request_review_comment`, `issues`,
  `issue_comment` and similar repository events arrive either way, and
  `check_run` is polled for pull requests the platform has seen. `check_suite`,
  `workflow_run`, `workflow_job`, `status`, `deployment`, `deployment_status`,
  `merge_group`, `workflow_dispatch`, `repository_dispatch` and the security
  alerts arrive **only** by webhook. A rule on one of those, on a deployment
  without webhooks, never fires and leaves no history.
- **Looking for a per-fire budget.** There is no spend limit on a trigger.
  Fire counts and cooldowns are the limits.
- **Reading inputs from the trigger history.** The history records the
  execution, not its inputs. The execution's `inputs` are in
  `GET /executions/{id}`.
- **Deleting to silence a rule.** Delete cannot be undone from the product;
  a paused rule can be resumed.

## Recommended tools and practices (as of 2026-10-04)

### Outcome: every rule is armed deliberately

- **Presets.** Ladders up by supplying a tested event, conditions, input
  mapping and limits in one command. Tradeoffs: without `-w` they dispatch
  `self-heal-pr`.
- **`POST /triggers` when input mapping is needed.** Ladders up because the
  CLI sends no input mapping, and a rule without one fires runs with no
  inputs and no repository. Tradeoffs: an API call, with the request shape
  in [references/http-api.md](references/http-api.md).
- **`syn triggers show` after every register.** Ladders up by reading back
  what was actually stored.

### Outcome: a fire or a non-fire is explained from the history

- **`syn triggers history`.** Ladders up by recording every decision with its
  guard and reason. Tradeoffs: it records the execution, not its inputs.
- **`GET /executions/{id}` for the fired run's `inputs`.** Ladders up by
  showing which mapped input was empty.

### Outcome: a noisy rule is disarmed, not deleted, while it is understood

- **`syn triggers pause` and `disable-all --force`.** Ladders up by stopping
  fires while keeping the rule and its history. The API also accepts a
  `reason` when pausing; the CLI does not send one.

Run `syn triggers <subcommand> --help` for the flags of the installed CLI
version.

## References

- [references/guards-and-presets.md](references/guards-and-presets.md): what
  each safety guard blocks, and each preset's event, condition, inputs and
  limits. Read when a rule is blocked or when choosing a preset.
- [references/http-api.md](references/http-api.md): every trigger route, and
  a complete `POST /triggers` body with conditions and input mapping. Read
  when the CLI's simple case is not enough.

## Continual improvement

File drift, gaps, or proposed updates at
https://github.com/syntropic137/syntropic137-skills/issues
