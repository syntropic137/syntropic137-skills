# Migration from `syntropic137-claude-plugin`

This document inventories every artifact in the Claude Code plugin
(`syntropic137/syntropic137-claude-plugin`), gives each one a single
disposition and a destination, and records how the two skills migrated so far
were checked against the product.

Inventory taken at plugin commit `e65ca7514baa8033156bd4b68566d5d99c994f02`
(plugin version `0.12.4`). Product surface checked against
`syntropic137/syntropic137` `main` at `366db9c0e7817b3e58f57285d25067bc5bab4bde`.

## Dispositions

| disposition | meaning |
|---|---|
| **migrate** | becomes a skill in this repo, rewritten against the current product surface |
| **merge** | its content goes into another skill, which owns it from then on |
| **keep as harness adapter** | stays in the plugin repo because it is Claude Code wiring (a slash command, hook, subagent or manifest). Its reusable knowledge is extracted into the named skill, and the adapter should end up as a thin pointer to that skill |
| **move to contributor docs** | it is for people working **on** Syntropic137 (`just` recipes, local dev stack, internals), so it belongs in `syntropic137/syntropic137` `docs/`, where repository paths are allowed |
| **retire** | not carried forward, with a reason |

Commands, hooks and agents are never copied into this repo: it holds skills
only (see the README).

## Skills (16)

| plugin path | disposition | destination | notes |
|---|---|---|---|
| `skills/syn-workflow/SKILL.md` | **migrate (this PR)** | `skills/syn-workflow/SKILL.md` | Rewritten. Stale items corrected below. |
| `skills/workflow-management/SKILL.md` | **merge**, split in two | CLI usage, registering and updating in place, the provenance refusals: merged into `skills/syn-workflow/SKILL.md` (this PR). YAML schema, phase design and prompt authoring: migrate later to `skills/authoring-workflows/SKILL.md` | The schema half needs its own verification against the workflow schema and was deliberately left out of this PR rather than carried over unchecked. |
| `skills/execution-control/SKILL.md` | **migrate (this PR)** | `skills/execution-control/SKILL.md` | Rewritten. Stale items corrected below. |
| `skills/syn-control/SKILL.md` | **merge (this PR)** | `skills/execution-control/SKILL.md` | Its cancel, stop, status and resume content overlapped entirely with execution-control. |
| `skills/troubleshooting-workflow-failures/SKILL.md` | **merge**, split in two | The diagnostic flow (read the execution, classify the failure, read the session, decide): merged into `skills/execution-control/SKILL.md` step 6 (this PR). `just health-check`, `just workspace-build` and local-stack fixes: move to contributor docs, `syntropic137/syntropic137` `docs/` | Only the steps that work against a deployed system were kept. |
| `skills/observability/SKILL.md` | **migrate** (later) | `skills/observing-sessions/SKILL.md` | Session, tool, token and cost observation through `syn sessions`, `syn observe`, `syn costs`. The two-lane architecture and event pipeline internals move to contributor docs. |
| `skills/syn-insights/SKILL.md` | **merge** (later) | `skills/observing-sessions/SKILL.md` | Same surface as observability, CLI-shaped. |
| `skills/session-discovery/SKILL.md` | **migrate** (later) | `skills/discovering-run-sessions/SKILL.md` | Finding every session of a run (`syn execution sessions`, transcripts). Its learning-loop section is **retired** in favour of `skills/mining-session-logs`, which already owns that job; no competing session-mining skill is created. |
| `skills/marketplace/SKILL.md` | **migrate** (later) | `skills/workflow-marketplace/SKILL.md` | Marketplace search, info, install and review before install. |
| `skills/syn-marketplace/SKILL.md` | **merge** (later) | `skills/workflow-marketplace/SKILL.md` | CLI-shaped duplicate of marketplace. |
| `skills/organization/SKILL.md` | **migrate** (later) | `skills/organization-hierarchy/SKILL.md` | Organizations, systems, repos. |
| `skills/syn-repo/SKILL.md` | **merge** (later) | `skills/organization-hierarchy/SKILL.md` | CLI-shaped subset of organization. |
| `skills/github-automation/SKILL.md` | **migrate** (later) | `skills/github-triggers/SKILL.md` | Trigger rules and their history through `syn triggers` and the API. Webhook tunnelling, smee and `just` recipes move to contributor docs. |
| `skills/syn-triggers/SKILL.md` | **merge** (later) | `skills/github-triggers/SKILL.md` | CLI-shaped subset of github-automation. |
| `skills/platform-ops/SKILL.md` | **move to contributor docs** | `syntropic137/syntropic137` `docs/` | Operating the platform's own stack (Docker Compose, `just`, service internals) is contributor knowledge, not product use. |
| `skills/setup/SKILL.md` | **split** | Dev-environment setup: move to contributor docs. Self-host install: stays with the plugin's `/syn-setup` adapter and the public docs site. Connection prerequisites (`SYN_API_URL`, credentials, `syn config show`, `syn health`): carried in the "Before you start" section of every migrated skill (this PR does so for both) | A consumer skill cannot run an installer that needs secrets typed outside the agent's context; the plugin's `!`-prefixed pattern is Claude-specific. |

## Commands (12): keep as harness adapters

Every command stays in the plugin: slash commands do not exist in Codex or the
other harnesses. Each should end up as a thin wrapper that runs the CLI and
defers to the named skill for judgement. The stale items listed are follow-ups
in the plugin repo; only those marked *verified* were checked in this PR.

| plugin path | disposition | knowledge lives in | follow-ups for the adapter |
|---|---|---|---|
| `commands/syn-run.md` | keep as harness adapter | `skills/syn-workflow` | Only exposes `--input`; add `-t`, `-R` and `--dry-run`, and stop passing repositories as inputs (*verified*: `repos` and `repository` are rejected as input keys). |
| `commands/syn-workflows.md` | keep as harness adapter | `skills/syn-workflow` | Maps `search` to `syn workflow search`, which searches marketplaces, not the deployment; its fallback `GET /workflows?q=` has no such parameter (*verified*). |
| `commands/syn-executions.md` | keep as harness adapter | `skills/execution-control` | Maps `status <id>` to `syn workflow status <id>`, which takes a workflow id, not an execution id; its fallback `/api/v1/executions/<id>/status` does not exist (*verified*). Use `syn execution show` or `/executions/<id>/state`. |
| `commands/syn-status.md` | keep as harness adapter | `skills/execution-control`, `skills/observing-sessions` | Not verified in this PR. |
| `commands/syn-health.md` | keep as harness adapter | every skill's "Before you start" (`syn health`) | Not verified in this PR. |
| `commands/syn-sessions.md` | keep as harness adapter | `skills/observing-sessions` (later) | Not verified in this PR. |
| `commands/syn-observe.md` | keep as harness adapter | `skills/observing-sessions` (later) | Not verified in this PR. |
| `commands/syn-costs.md` | keep as harness adapter | `skills/observing-sessions` (later) | Not verified in this PR. |
| `commands/syn-metrics.md` | keep as harness adapter | `skills/observing-sessions` (later) | Not verified in this PR. |
| `commands/syn-triggers.md` | keep as harness adapter | `skills/github-triggers` (later) | Not verified in this PR. |
| `commands/syn-marketplace.md` | keep as harness adapter | `skills/workflow-marketplace` (later) | Not verified in this PR. |
| `commands/syn-setup.md` | keep as harness adapter | public docs; contributor docs for the dev path | Uses Claude's `!` external-execution prefix so secrets never enter the context window. That property is the reason it must stay Claude-specific. |

## Agents (2): keep as harness adapters

| plugin path | disposition | knowledge lives in | notes |
|---|---|---|---|
| `agents/execution-monitor.md` | keep as harness adapter | `skills/execution-control` (steps 2 and 3: read, follow live, confirm) | A Claude subagent definition (model, disallowed tools). Its fixed cost alert thresholds are policy, not product, and were not carried into the skill. It references `/syn-observe`, a slash command. |
| `agents/security-reviewer.md` | keep as harness adapter | `skills/workflow-marketplace` (later): review a package before installing it | A Claude subagent definition (model, allowed tools). |

## Hooks: keep as harness adapter

| plugin path | disposition | knowledge lives in | notes |
|---|---|---|---|
| `hooks/hooks.json` | keep as harness adapter | n/a | Registers a Claude Code `SessionStart` hook. Codex has no equivalent. |
| `hooks/handlers/session-start.py` | keep as harness adapter | every skill's "Before you start" (`syn health`, `syn config show`) | Calls the health endpoint and suggests `/syn-setup` and `/syn-status` on failure. Resolved through `CLAUDE_PLUGIN_ROOT`. |

## Manifest and other files

| plugin path | disposition | notes |
|---|---|---|
| `.claude-plugin/plugin.json` | keep in the plugin | Claude Code plugin manifest (name `syntropic137`, version `0.12.4`, `commands` and `skills` paths). When migrated skills are removed from the plugin, its `skills` path should instead point at, or vendor, this repo. |
| `.claude-plugin/marketplace.json` | keep in the plugin | Follow-up: its plugin entry says version `0.9.0`, stale against `plugin.json`'s `0.12.4`. |
| `CLAUDE.md`, `README.md`, `SECURITY.md` | keep in the plugin | Describe the plugin itself. `SECURITY.md`'s rule that secrets never enter the context window applies to every skill here too, and none of the migrated skills asks for a secret value. |
| `scripts/validate_yaml_examples.py` | keep in the plugin | Validates the plugin's YAML examples against the platform schema. A future `skills/authoring-workflows` will need the same check here. |
| `scripts/syn137-banner-claude-plugin.html`, `public/assets/` | keep in the plugin | Branding assets. |
| `.github/workflows/` | keep in the plugin | Plugin tagging and version checks. Not touched. |
| `.gitattributes`, `.gitignore` | keep in the plugin | Repo housekeeping. |

## Stale instructions corrected in this PR

Each of these was in the plugin source and would have been wrong if copied.

### `syn-workflow` (from `syn-workflow` and `workflow-management`)

1. `syn workflow status <execution-id>`: the argument is a **workflow** id, and
   the command lists that workflow's runs. One execution is read with
   `syn execution show <execution-id>`.
2. Slash commands `/syn-workflow`, `/syn-health`, `/syn-control`: replaced with
   `syn health` and references to the `execution-control` skill.
3. `argument-hint` and `model: sonnet` frontmatter: Claude-only, removed. The
   frontmatter is `name` and `description` only, like `mining-session-logs`.
4. The CLI now **refuses** `-t` when no phase prompt consumes the task. The
   plugin skill did not say so; the new skill documents it with the other
   pre-dispatch checks, and `--dry-run`, which it also omitted.
5. Pointer to the workflow-management skill's section for the provenance
   refusal: replaced with a self-contained table of the four refusals and the
   right response to each, including that `--force` does not bypass the
   no-version refusal.
6. `syn workflow search` presented as a way to find workflows: it searches
   marketplaces. The new skill says so and uses `syn workflow list`.

### `execution-control` (from `execution-control`, `syn-control`, `troubleshooting-workflow-failures`)

1. `--max-budget-usd 5.00`: no such flag exists on `syn workflow run`.
2. `"max_budget_usd": 5.00` in the execute request: the field is deprecated and
   ignored. The skill now says there is no per-execution spend cap.
3. "FAILED with budget error / max_budget_usd hit" as a failure cause: removed,
   since no budget cap exists to hit.
4. `--input repository=owner/repo`: rejected by the CLI and the API.
   Repositories go on `-R`.
5. `inject` presented as a working way to steer a running agent, via a `curl`
   with no auth header and no content type: the inject request is accepted
   and queued, but nothing delivers the message to the agent. The only
   consumer of the control-signal queue acts on cancel signals alone; inject
   signals are dequeued and dropped, and the stored message is never read.
   The skill now says not to rely on it. **Follow-up for syntropic137:** this
   is the same defect class as the deleted `pause` (accepted, ineffective),
   and no tracking issue was found for it. It should be filed against
   `syntropic137/syntropic137` (related: #777, interactive steering). This PR
   does not file it.
6. "Cancel marks remaining phases SKIPPED": nothing in the cancel path sets
   `skipped`. Removed. The skill tells you to confirm the cancel by reading
   the execution until it shows `cancelled`.
7. "Phase stuck RUNNING means a timeout": unsupported. Removed.
8. The monitoring section said the phase table shows each phase's session id;
   the troubleshooting section said the session id is in the show output; and
   the inspection step said artifacts are listed by `syn execution show`. None
   of these is true. The phase table has no session id, artifact id or phase
   error; those come from `GET /executions/{id}` (`phases[].session_id`,
   `phases[].artifact_id`, `phases[].error_message`), which the skill now
   uses.
9. `TOOL_BLOCKED` "in the tool timeline": `syn observe tools` shows only ok or
   error. A blocked call is the `tool_blocked` operation type in
   `syn sessions show`.
10. `syn control status` used for phase detail in troubleshooting: it prints
    only the id and state.
11. `curl http://localhost:8137/api/v1/executions` with no auth: replaced with
    `$SYN_API_URL/api/v1` and an `Authorization` header.
12. `just workspace-build`, `just health-check`: contributor commands, not
    product surface. Removed (see dispositions above).
13. "Processor To-Do List" and handler idempotency: internal architecture,
    not product. Removed.
14. Slash commands `/syn-insights`, `/syn-control`: replaced with the skills
    that will hold that knowledge.
15. Added what was missing and is true: resume inherits only the unbroken
    prefix of completed phases; one resume per execution;
    `--acknowledge-external-effects` is required whenever the resumed phase
    ever started; the resume is accepted before the child starts, and the
    parent's `Resume start` block is where a child that never appears is
    explained; the `Deliverable` and `Side effects` outcome lines; and
    `failure_classification` versus `reported_failure_reason`.

## Verification against `syntropic137/syntropic137` main

Every command, flag, endpoint and response field the two skills name, with
where it was found. Paths are in `syntropic137/syntropic137` at the commit
above. The CLI is `apps/syn-cli-node/src/commands/`, abbreviated `cli/`. The
API is `apps/syn-api/src/syn_api/`, abbreviated `api/`.

### CLI

| surface | found in |
|---|---|
| `syn config show`; `SYN_API_URL` default `http://localhost:8137`; `SYN_API_TOKEN`, `SYN_API_USER`, `SYN_API_PASSWORD` | `cli/config.ts`; `apps/syn-cli-node/src/config.ts`; `apps/syn-cli-node/src/constants.ts` |
| `/api/v1` prefix appended by the client | `apps/syn-cli-node/src/client/constants.ts` (`API_PREFIX`) |
| `syn health` | `cli/health.ts` |
| `syn workflow list [--include-archived]`, `show`, `validate`, `delete --force`, `create [--from] [--type --description --repo --ref --repos --no-repos]` | `cli/workflow/crud.ts` |
| `syn workflow run -t -i -R -n/--dry-run -q/--quiet`; reserved `repos`/`repository`; missing-required error; discarded-input warning; `requires_repos` warning; unconsumed `-t` refusal; empty-task warning; `Execution ID` | `cli/workflow/run.ts` |
| `syn workflow status <workflow-id>` (reads `/workflows/{id}/runs`) | `cli/workflow/run.ts` |
| `syn run` shortcut | `apps/syn-cli-node/src/registry.ts` (registers `runCommand` at the root) |
| `syn workflow install <source> --ref (default main) -n --force`; `packages` | `cli/workflow/install.ts` |
| `syn workflow update <name> --ref -n --force`; `uninstall <name> --keep-workflows` | `cli/workflow/update.ts` |
| `syn workflow search`, `info` (marketplaces) | `cli/workflow/search.ts` |
| `syn execution list -s/--status --page --page-size`; `show`; `resume --override-cancellation --acknowledge-external-effects`; the show fields and the `Resume start` block | `cli/execution.ts` |
| `syn execution sessions --all --json --phase` | `cli/execution-sessions.ts` |
| `syn control cancel -r -f`, `stop -r -f`, `status`, `inject -m` | `cli/control.ts` |
| `syn watch execution`, `syn watch activity` | `cli/watch.ts` |
| `syn sessions list --execution`, `syn sessions show` (operation type, error) | `cli/sessions.ts` |
| `syn observe tools`, `syn observe tokens` | `cli/observe.ts` |
| `syn artifacts show`, `syn artifacts content` | `cli/artifacts.ts` |
| `syn repo list` | `cli/repo.ts` |

### API

| surface | found in |
|---|---|
| `GET /workflows` params `workflow_type`, `include_archived`, `page`, `page_size`, `order_by` (no `q`) | `api/routes/workflows/queries.py` |
| `GET /workflows/{id}`, `GET /workflows/{id}/runs` | `api/routes/workflows/queries.py` |
| `POST /workflows/{id}/execute` body `inputs`, `task`, `repos`; deprecated ignored `provider`, `max_budget_usd`; response `execution_id`, `workflow_id`, `status`, `message` | `api/routes/executions/commands.py` (`ExecuteWorkflowRequest`, `ExecuteWorkflowResponse`) |
| `GET /workflows/executions/active` | `api/routes/executions/commands.py` (router prefix `/workflows`) |
| `GET /executions` params `status`, `statuses`, `page`, `page_size`; `GET /executions/{id}` | `api/routes/executions/queries.py` |
| `ExecutionDetailResponse` fields `error_message`, `failure_classification`, `reported_failure_reason`, `deliverable_produced`, `reported_side_effects`, `artifact_ids`, `resume_start`; `phases[]` fields `session_id`, `agent_session_ids`, `artifact_id`, `error_message`, `deliverable_recovered` | `api/routes/executions/models.py` |
| `ResumeStartInfo` statuses `pending`, `paused`, `retryable`, `dispatched`, `started`, `failed`; `status_reason`, `attempts`, `max_attempts` | `api/routes/executions/models.py` |
| `POST /executions/{id}/cancel`, `POST /executions/{id}/inject`, `GET /executions/{id}/state` (no `/status` route) | `api/routes/executions/control.py` |
| `POST /executions/{id}/resume` body and response fields | `api/routes/executions/resume.py` |
| `GET /executions/{id}/session-inventory` | `api/routes/executions/inventory.py` |

### Domain behaviour the skills state

| claim | found in |
|---|---|
| execution statuses `not_started`, `running`, `completed`, `failed`, `cancelled`, `interrupted`; no `paused` | `ExecutionStatus` in `packages/syn-domain/.../aggregate_execution/value_objects.py` |
| phase statuses `pending`, `running`, `completed`, `failed`, `skipped` | `PhaseStatus` in the same file |
| cancel and inject accepted only while running | `WorkflowExecutionAggregate` (control signal guard) and `packages/syn-adapters/src/syn_adapters/control/controller.py` |
| resume rules: failed and interrupted resumable, cancelled with override, one resume per execution, contiguous completed prefix inherited, external-effects acknowledgement when the phase ever started | `WorkflowExecutionAggregate` resume handler and its tests |
| inject not delivered | `CancelSignalPoller` acts only on `CANCEL`; `inject_message` is written and read by the Redis control adapter and read nowhere else in `packages`, `apps` or `lib` |
| `tool_blocked` operation type | `packages/syn-domain/.../agent_sessions/_shared/value_objects.py` |
| install provenance refusals and messages | `packages/syn-domain/.../aggregate_workflow_template/errors.py` |

## Harness discovery

See the pull request description for the exact commands and output used to
check that Claude Code and Codex both discover the migrated skills from a
local checkout.
