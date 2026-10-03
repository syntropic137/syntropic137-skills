---
name: github-triggers
description: Use when making a Syntropic137 workflow run automatically on GitHub events, or managing the trigger rules that do so - registering a rule or enabling a built-in preset, choosing its event, conditions, input mapping and safety limits, pausing, resuming or deleting rules, and working out why a trigger did or did not fire. Trigger phrases include "run this workflow on every PR", "auto-fix failing CI", "self-healing", "respond to review comments", "/syn comment command", "set up a trigger", "why didn't my trigger fire", "trigger fired too often", "pause the trigger", "stop all triggers on this repo", "trigger history", "syn triggers". Do NOT use for starting a workflow by hand (use syn-workflow), for following or cancelling the executions a trigger started (use execution-control), or for installing the GitHub App or exposing a webhook URL, which is deployment setup rather than product use.
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

## Before you start

Every command talks to one deployment. Check which one:

```bash
syn config show     # SYN_API_URL and whether credentials are set
syn health
```

`SYN_API_URL` defaults to `http://localhost:8137`. Credentials are
`SYN_API_TOKEN` (bearer) or `SYN_API_USER` + `SYN_API_PASSWORD` (basic).

The deployment's GitHub App must be installed on the repository:
`syn github repos` lists the repositories it can reach. The workflow must be
registered: `syn workflow list` (see the syn-workflow skill).

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
3. **Safety guards**, each recorded by name when it blocks:

| guard | blocks when |
|---|---|
| `max_attempts` | this rule has fired `max_attempts` times for this pull request |
| `cooldown` | this rule fired for this pull request less than `cooldown_seconds` ago |
| `daily_limit` | this rule has fired `daily_limit` times today |
| `idempotency` | this delivery was already processed |
| `concurrency` | an execution this rule started for this pull request is still running |
| `dispatch_rate_limit` | the deployment is starting too many triggered runs per minute |

A blocked event is not retried later. Different rules do not block each other
on the same pull request.

4. **Input mapping.** Each workflow input is read from a payload path, for
   example `"pr_number": "pull_request.number"`. A path that resolves to
   nothing is left out. An input named `repository` holding `owner/repo`
   also becomes the repository the run checks out.

## Principles

- **Prefer a preset when one fits.** Presets carry a tested event, conditions,
  input mapping and limits.
- **The CLI registers the simple case.** `syn triggers register` sets the
  event, repository, workflow, `eq` conditions, `max_attempts` and
  `cooldown_seconds`. It sends no input mapping, a `daily_limit` of 20 and a
  generated name. Anything more is the API.
- **Pause before you delete.** Pausing keeps the rule and its history.
- **Destructive commands need `--force`.** `syn triggers delete` and
  `syn triggers disable-all` refuse without it.

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

## The procedure

### 1. Enable a preset

```bash
syn triggers enable self-healing -r owner/repo [-w <workflow-id>]
```

| preset | event | fires when | inputs mapped | limits |
|---|---|---|---|---|
| `self-healing` | `check_run.completed` | the check failed and belongs to a pull request | `repository`, `pr_number`, `branch`, `check_name`, `check_output_title`, `check_output_summary`, `check_html_url` | 3 attempts, 20 a day, 300 s cooldown |
| `review-fix` | `pull_request_review.submitted` | the review requested changes or commented, on a non-draft pull request | `repository`, `pr_number`, `branch`, `review_body`, `reviewer`, `review_html_url` | 2 attempts, 10 a day, 600 s cooldown |
| `comment-command` | `issue_comment.created` | a pull request comment contains `/syn` | `repository`, `pr_number`, `pr_title`, `comment_body`, `comment_author`, `comment_id`, `comment_html_url` | 5 attempts, 30 a day, 60 s cooldown |

Without `-w`, a preset dispatches the deployment's `self-heal-pr` workflow.
Enabling the same preset twice on a repository is refused.

### 2. Register a rule

The simple case, from the CLI:

```bash
syn triggers register -r owner/repo -w <workflow-id> -e pull_request.opened \
  -c pull_request.base.ref=main --max-attempts 3 --cooldown 300
```

`-c field=value` repeats, and each is an `eq` condition. `--max-attempts`
defaults to 5 and `--cooldown` to 300 seconds.

With input mapping, other operators, a name or a different daily limit, use
the API:

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
API="$SYN_API_URL/api/v1"
curl -sf -H "$AUTH" -H "Content-Type: application/json" -X POST "$API/triggers" -d '{
  "name": "review-new-prs",
  "event": "pull_request.opened",
  "repository": "owner/repo",
  "workflow_id": "<workflow-id>",
  "conditions": [
    {"field": "pull_request.draft", "operator": "eq", "value": "false"},
    {"field": "pull_request.base.ref", "operator": "eq", "value": "main"}
  ],
  "input_mapping": {
    "repository": "repository.full_name",
    "pr_number": "pull_request.number",
    "branch": "pull_request.head.ref"
  },
  "config": {"max_attempts": 3, "daily_limit": 20, "cooldown_seconds": 300}
}'
```

Then read it back:

```bash
syn triggers show <trigger-id>
syn triggers list -r owner/repo        # -s active|paused|deleted, -a includes deleted
```

### 3. Why didn't it fire?

```bash
syn triggers history <trigger-id>      # -n, default 20
```

- **A `blocked` entry** names the guard and the reason. `conditions_not_met`
  means the payload did not match: compare the conditions in
  `syn triggers show` with the event's payload.
- **No entry at all** means no event reached this rule. Check the rule's event
  spelling (`<event>.<action>`), its repository (`owner/repo`), that it is
  `active`, and whether its event arrives without webhooks (anti-patterns
  above).

### 4. Why did it fire and do nothing?

The history's execution id is the run. Read it with the execution-control
skill. Then read its `inputs` (`GET /executions/{id}`) against the inputs the
workflow needs: a missing input is a missing or wrong `input_mapping` path.

### 5. Stop a rule

```bash
syn triggers pause <trigger-id>
syn triggers resume <trigger-id>
syn triggers disable-all -r owner/repo --force   # pauses every active rule on the repository
syn triggers delete <trigger-id> --force         # permanent
```

`disable-all` pauses; resume rules one by one.

## Recommended tools and practices (as of 2026-10-03)

| endpoint | does |
|---|---|
| `POST /triggers` | register: `name`, `event`, `repository`, `workflow_id`, `conditions[]` (`field`, `operator`, `value` as a string), `input_mapping`, `config` (`max_attempts` default 3, `daily_limit` 20, `cooldown_seconds` 300) |
| `POST /triggers/presets/{preset_name}` | enable a preset: `repository`, optional `workflow_id` |
| `GET /triggers` | list; params `repository`, `status` |
| `GET /triggers/{id}` | `name`, `event`, `repository`, `workflow_id`, `status`, `fire_count`, `conditions`, `input_mapping`, `config`, `last_fired_at` |
| `GET /triggers/{id}/history` | `entries[]`: `fired_at`, `execution_id`, `event_type`, `pr_number`, `status`, `cost_usd`, `guard_name`, `block_reason`; param `limit` |
| `PATCH /triggers/{id}` | `{"action": "pause", "reason": "..."}` or `{"action": "resume"}` |
| `DELETE /triggers/{id}` | delete |

The API accepts a `reason` when pausing; the CLI does not send one.

Run `syn triggers <subcommand> --help` for the flags of the installed CLI
version.
