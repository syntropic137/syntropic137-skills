# Migration from `syntropic137-claude-plugin`

This document inventories every artifact in the Claude Code plugin
(`syntropic137/syntropic137-claude-plugin`), gives each one a single
disposition and a destination, and records how each migrated skill was
checked against the product.

Inventory taken at plugin commit `e65ca7514baa8033156bd4b68566d5d99c994f02`
(plugin version `0.12.4`). Product surface checked against
`syntropic137/syntropic137` `main` at `366db9c0e7817b3e58f57285d25067bc5bab4bde`
for `syn-workflow` and `execution-control`, and at
`c1ab5a4b` (no product-surface change since `366db9c`) for
`observing-sessions`, `discovering-run-sessions` and `github-triggers`,
and at `8901e12c1294be75d8cd7e9e71af57859789475b` for `workflow-marketplace`,
`organization-hierarchy` and `authoring-workflows`.

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
| `skills/workflow-management/SKILL.md` | **merge**, split in two | CLI usage, registering and updating in place, the provenance refusals: merged into `skills/syn-workflow/SKILL.md` (this PR). YAML schema, phase design and prompt authoring: **migrated** to `skills/authoring-workflows/SKILL.md` | Every schema key in the authoring half was checked against the workflow definition models on main; see "Stale instructions corrected" for what changed. |
| `skills/execution-control/SKILL.md` | **migrate (this PR)** | `skills/execution-control/SKILL.md` | Rewritten. Stale items corrected below. |
| `skills/syn-control/SKILL.md` | **merge (this PR)** | `skills/execution-control/SKILL.md` | Its cancel, stop, status and resume content overlapped entirely with execution-control. |
| `skills/troubleshooting-workflow-failures/SKILL.md` | **merge**, split in two | The diagnostic flow (read the execution, classify the failure, read the session, decide): merged into `skills/execution-control/SKILL.md` step 6 (this PR). `just health-check`, `just workspace-build` and local-stack fixes: move to contributor docs, `syntropic137/syntropic137` `docs/` | Only the steps that work against a deployed system were kept. |
| `skills/observability/SKILL.md` | **migrated** | `skills/observing-sessions/SKILL.md` | Rewritten. Session, tool, token and cost observation through `syn sessions`, `syn observe`, `syn costs`, `syn metrics`. The two-lane architecture and event pipeline internals move to contributor docs. Stale items corrected below. |
| `skills/syn-insights/SKILL.md` | **merged** | `skills/observing-sessions/SKILL.md` | Same surface as observability, CLI-shaped. `syn insights` is in the skill's view table. |
| `skills/session-discovery/SKILL.md` | **migrated** | `skills/discovering-run-sessions/SKILL.md` | Rewritten. Finding every session of a run (`syn execution sessions`, transcripts). Its learning-loop section is **retired** in favour of `skills/mining-session-logs`, which already owns that job; no competing session-mining skill is created. |
| `skills/marketplace/SKILL.md` | **migrated** | `skills/workflow-marketplace/SKILL.md` | Marketplace search, info, install and review before install. |
| `skills/syn-marketplace/SKILL.md` | **merged** | `skills/workflow-marketplace/SKILL.md` | CLI-shaped duplicate of marketplace. |
| `skills/organization/SKILL.md` | **migrated** | `skills/organization-hierarchy/SKILL.md` | Organizations, systems, repos. |
| `skills/syn-repo/SKILL.md` | **merged** | `skills/organization-hierarchy/SKILL.md` | CLI-shaped subset of organization. |
| `skills/github-automation/SKILL.md` | **migrated** | `skills/github-triggers/SKILL.md` | Rewritten. Trigger rules and their history through `syn triggers` and the API. GitHub App installation, webhook tunnelling, Smee and `just` recipes move to contributor docs. Stale items corrected below. |
| `skills/syn-triggers/SKILL.md` | **merged** | `skills/github-triggers/SKILL.md` | CLI-shaped subset of github-automation. |
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
| `commands/syn-sessions.md` | keep as harness adapter | `skills/observing-sessions` | The command itself was not verified; the stale items found in the observability skill below are likely to recur in it. |
| `commands/syn-observe.md` | keep as harness adapter | `skills/observing-sessions` | The command itself was not verified; the stale items found in the observability skill below are likely to recur in it. |
| `commands/syn-costs.md` | keep as harness adapter | `skills/observing-sessions` | The command itself was not verified; the stale items found in the observability skill below are likely to recur in it. |
| `commands/syn-metrics.md` | keep as harness adapter | `skills/observing-sessions` | The command itself was not verified; the stale items found in the observability skill below are likely to recur in it. |
| `commands/syn-triggers.md` | keep as harness adapter | `skills/github-triggers` | The command itself was not verified. Its sibling skill used `--name`, `--event`, `--repository`, `--budget`, `--max-fires` and `pause --reason`, none of which exist (*verified*, see below); check the command for the same. |
| `commands/syn-marketplace.md` | keep as harness adapter | `skills/workflow-marketplace` (migrated) | Its knowledge now lives in the skill; the command stays as the Claude entry point. |
| `commands/syn-setup.md` | keep as harness adapter | public docs; contributor docs for the dev path | Uses Claude's `!` external-execution prefix so secrets never enter the context window. That property is the reason it must stay Claude-specific. |

## Agents (2): keep as harness adapters

| plugin path | disposition | knowledge lives in | notes |
|---|---|---|---|
| `agents/execution-monitor.md` | keep as harness adapter | `skills/execution-control` (steps 2 and 3: read, follow live, confirm) | A Claude subagent definition (model, disallowed tools). Its fixed cost alert thresholds are policy, not product, and were not carried into the skill. It references `/syn-observe`, a slash command. |
| `agents/security-reviewer.md` | keep as harness adapter | `skills/workflow-marketplace` (migrated): step 3, review a package before installing it | A Claude subagent definition (model, allowed tools). |

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
| `scripts/validate_yaml_examples.py` | keep in the plugin | Validates the plugin's YAML examples against the platform schema. `skills/authoring-workflows` now has YAML examples too; its complete example was checked with `WorkflowDefinition.from_yaml` and `validate_workflow_yaml` on main, but this repo has no automated check for it yet. |
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

### `observing-sessions` (from `observability` and `syn-insights`)

1. `syn costs execution <workflow-id>`: the argument is an **execution** id.
2. The tool timeline described as showing each tool's input and output:
   `syn observe tools` shows time, tool, duration and ok or error only. Input
   and output are `operations[].tool_input` and `tool_output` in
   `GET /sessions/{id}`.
3. `TOOL_BLOCKED` in `syn observe tools`: a blocked call is the `tool_blocked`
   operation type in `syn sessions show`.
4. Token fields `total_input_tokens` and `total_output_tokens`: the
   observability tokens response uses `input_tokens` and `output_tokens`.
5. `unpriced_tokens` and `vendor_cost_usd` as fields to read: neither is in
   any cost response. The API has `unpriced_observation_count` and
   `unpriced_by_phase`; the CLI shows `unpriced` or `>=$X (partial)`.
6. "A codex phase with no model is unpriced": an unset codex model is given
   the platform's default codex model when the workflow is installed, and is
   priced as that. Unpriced means the model that ran has no rate.
7. "Default pricing $0.01 per 1K input, $0.03 per 1K output": no such
   default exists. Removed.
8. `syn insights overview` described as calling `/organizations/overview` and
   showing executions and costs: it calls `/insights/overview` and shows
   systems, repos, unassigned repos and active executions.
9. `syn artifacts content --raw`: no such flag.
10. `syn sessions list --workflow` returning "most recent first": the order
    was not confirmed. Dropped.
11. The two-lane architecture and event pipeline internals (hook watcher,
    collector port, TimescaleDB, projections, SHA-256 dedup): contributor
    material. Removed.
12. Slash commands `/syn-insights`, `/syn-control`, `/syn-health`: replaced
    with skills and `syn health`.
13. `argument-hint` and `model: sonnet` frontmatter: removed.
14. `curl http://localhost:8137/...` with no auth: replaced with
    `$SYN_API_URL/api/v1` and an `Authorization` header.
15. "Compare opus versus sonnet in `cost_by_model`": the keys are the model ids
    the harness reported, and cost with no reported model is under
    `unattributed-model`. `tokens_by_tool` is API-only and an estimate.

### `discovering-run-sessions` (from `session-discovery`)

The plugin skill's commands, flags, statuses and routes were all found on
main. What changed:

1. The learning-loop section: retired in favour of `mining-session-logs`.
2. Pointers to the troubleshooting-workflow-failures, workflow-management and
   observability skills: replaced with `execution-control`,
   `observing-sessions` and `mining-session-logs`.
3. `summary.complete` and the CLI's top-level `complete` were used
   interchangeably: the first is the server's coverage verdict, the second
   adds that this read covered every section unfiltered. The skill now
   distinguishes them.
4. `syn execution sessions --refresh` was not mentioned; it is the one
   inventory command that writes. Documented as such.
5. A sentence the first draft of this migration added, that nodes carry a
   `confidence`, was wrong: only edges, memberships and bindings do. Fixed
   before commit.

### `github-triggers` (from `github-automation` and `syn-triggers`)

1. `syn triggers register --name --event --repository --max-fires --budget`:
   the flags are `-r/--repo`, `-w/--workflow`, `-e/--event`,
   `-c/--condition`, `--max-attempts` and `--cooldown`. There is no name,
   budget or max-fires flag; the CLI generates the name.
2. `budget_per_trigger_usd` as a safety limit: no such field. A trigger has no
   spend limit.
3. `--event pull_request --condition action=opened`: the platform matches the
   compound `pull_request.opened` exactly. That rule would never fire.
4. `--condition base.ref=main`: conditions are paths from the payload root,
   so `pull_request.base.ref`.
5. `"operator": "equals"`: the operator is `eq`. The full set is `eq`, `neq`,
   `in`, `not_in`, `contains`, `not_empty`, `is_empty`.
6. The CLI shown setting input mapping implicitly: `syn triggers register`
   sends no `input_mapping` and a fixed `daily_limit` of 20. Mapping, other
   operators and other limits are `POST /triggers`.
7. "`{{repository}}` in the template's `repository.url` clones the triggering
   repo": an input named `repository` holding `owner/repo` becomes the run's
   repository. The template claim is removed.
8. "Check `syn triggers history` for what was passed as inputs": history does
   not record inputs. They are the execution's `inputs` in
   `GET /executions/{id}`.
9. `syn triggers pause <id> --reason`: the CLI has no `--reason`. The API's
   `PATCH /triggers/{id}` accepts one.
10. `syn triggers list --repository` and `enable <name> --repository`: the flag
    is `-r/--repo`.
11. `curl -X DELETE http://localhost:8137/...` "if the CLI doesn't support
    delete": it does, with `--force`. Removed.
12. "Supported events: push, pull_request, issues, issue_comment, check_run,
    workflow_run": `workflow_run` arrives only by webhook, `check_run` by
    webhook or Checks API polling. The skill now says which events need a
    reachable webhook URL.
13. Guards listed as concurrency, max_attempts, cooldown, daily_limit: the
    full set also has `idempotency` and `dispatch_rate_limit`. The
    `cross_trigger_cooldown` guard exists but its window is 0, so it never
    blocks; the skill says rules do not block each other. Production wires no
    debouncer, so a retryable block is recorded, not retried later.
14. GitHub App setup (`npx @syntropic137/setup github-app`, `just onboard-dev`,
    `just setup-stage`, `just dev-webhooks`), Smee and the Cloudflare tunnel:
    deployment and contributor setup, not product use. Removed.
15. `TriggerRuleAggregate` in the flow diagram: internal. Removed.
16. `/syn-triggers`, `/syn-health`, `argument-hint`, `model: sonnet`:
    removed.

### `workflow-marketplace` (from `marketplace`, `syn-marketplace` and `agents/security-reviewer.md`)

1. `syn workflow export <id> --output ./workflow.yaml`: `-o/--output` is a
   directory (default `./<slug>-export`), and `-f/--format` is
   `package` or `plugin`.
2. "Push a `workflows/` directory to GitHub, then `syn marketplace add` it":
   `marketplace add` refuses a repository without `marketplace.json` at its
   root. The skill documents the index format.
3. `triggers.json` in a package, and reviewing it: nothing in the CLI reads
   that file. Removed.
4. The list of workflows in the default marketplace: not verifiable from the
   product. Removed.
5. Ref precedence was not stated, and `--ref main` reads like an override: a
   plugin entry's pinned `ref` wins over the default `main`. Stated.
6. Search silently skipping a marketplace whose index fails to fetch, and
   install not being transactional: not mentioned. Added as anti-patterns.
7. `install --dry-run` presented as validation: it resolves the package
   locally and does not ask the deployment. The skill validates with
   `syn workflow validate` on the package directory instead, since a single
   file inside a package cannot resolve `prompt_file`.
8. Security reviewer: "a codex phase with no `model` runs unpriced": the
   model is defaulted at install. Removed. Its example declaring `read`: a
   lowercase name outside the tool vocabulary is rejected; the check is now
   "declared vs instructed". "Budget" as a trigger safety limit: no such
   limit. Removed.
9. Reviewing `claude_plugins` and `skills` entries, which pull more code in
   at run time, and `sandbox: full-access` being the codex default: not in
   the source. Added to the review table.
10. `/syn-health`, `/syn-marketplace`, "use the security-reviewer agent",
    `argument-hint`, `model: sonnet`: Claude only. Removed.
11. Reviewing and validating the cloned marketplace repository as the
    package (caught in verification of this migration): a marketplace root
    holds `marketplace.json` and package directories, and `syn workflow
    validate` refuses it with "No workflow files found". The skill now
    reviews and validates the entry's `source` path, which `info` prints.

### `organization-hierarchy` (from `organization` and `syn-repo`)

1. `syn organization create`: the command group is `syn org`.
2. `syn system create --organization`: the flag is `-o/--org`, and it is
   required.
3. Repos auto-registered by the GitHub App on first webhook: not on main.
   Registration is explicit, through `syn repo register` (`POST /repos`).
4. "Assigning an already assigned repo fails silently": it is refused with
   "Repo is already assigned to a system" (409). Unassign first.
5. `syn repo register --system` presented as working: the flag is accepted
   and never sent. Stated as an anti-pattern; assign separately.
6. `/organizations/overview`: no such route. Deployment wide rollups are
   `/insights/overview`, `/insights/cost`, `/insights/contribution-heatmap`.
7. "Set up the hierarchy before triggers so cost is attributed": cost is
   keyed by the repository's `owner/repo` name and correlated from
   executions, so it does not depend on registration order. Removed.
8. curl examples had no `Authorization` header. Added.
9. Read model class names, `npx @syntropic137/setup github-app` and
   `SYN_PUBLIC_HOSTNAME` in a local env file: internal or setup material.
   Removed.
10. Deregistering a repo: not covered. Added `DELETE /repos/{id}` (no CLI
    command; refused while active triggers exist).
11. `/syn-repo`, `argument-hint`, `model`: Claude only. Removed.

### `authoring-workflows` (from the schema half of `workflow-management`)

1. `type` presented as a validated enum: it is free text, and a value
   outside the six known types is stored as `custom` without an error.
2. `requires_repos` "inferred when omitted": it defaults to true when
   omitted. Stated as Trap 1.
3. `can_open_pr` "inert since #1478 ... (#1492)": it is retired, accepted,
   dropped and reported as a notice. Stated without issue numbers.
4. "A codex phase with no model lands in `unpriced_tokens`": no such field,
   and the model is defaulted at install. Removed.
5. `CODEX_AUTH_JSON` in the platform `.env`: deployment configuration, not
   authoring. Removed.
6. Escalation via `syn control status <exec-id>` to read each phase's
   `artifact_id`: control status prints only the id and state. Removed;
   execution-control covers diagnosis.
7. A codex model id named in an example: not verifiable from the product.
   Replaced with "a concrete model id".
8. `allowed_tools` under `agent:`: not in the source, but the most common
   failure (#1081). The agent block forbids unknown keys, so it is rejected.
   Stated as Trap 3, with a wrong and right example.
9. `$ARGUMENTS` source: stated only in passing. Stated as Trap 2, including
   the refusal of `-t` when no prompt consumes the task. The first draft of
   this migration said only `-t` fills it (caught in verification):
   `-i task=value` also does, `-t` wins when both are passed, and a
   declared `task` default fills it when neither is.
10. Not in the source and added: `max_tokens` rejected, `sandbox: read-only`
    refused, `execution_type` other than `sequential` rejected, reserved
    input names, `input_artifacts` must resolve, prompt file frontmatter
    merge, `shared://`, the `{{repos}}` and `{{<phase-id>}}` placeholders and
    the 2000 character cut, pinned plugin and skill references with
    `@latest` rejected.
11. Scaffolding with `syn workflow init` and validating straight away
    (caught in verification of this migration): every generated prompt file
    carries `max-tokens: 4096` in its frontmatter, which is read as the
    rejected `max_tokens`, so an untouched scaffold fails validation. The
    skill tells authors to delete that line first. The generator itself
    still needs fixing in the product.

## Verification against `syntropic137/syntropic137` main

Every command, flag, endpoint and response field the migrated skills name,
with where it was found. Paths are in `syntropic137/syntropic137` at the commit
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
| `syn sessions list --execution -w/--workflow -s/--status -n/--limit`, `syn sessions show` (status, provider, model, tokens, cost, error, operations) | `cli/sessions.ts` |
| `syn observe tools <session-id> --limit` (time, tool, duration, ok or error), `syn observe tokens` (input, output, total, cache creation, cache read, estimated cost) | `cli/observe.ts` |
| `syn costs summary`, `sessions [-e]`, `session`, `executions`, `execution <execution-id>`; `unpriced` and `>=$X (partial)` display | `cli/costs.ts` |
| `syn metrics show [-w]` | `cli/metrics.ts` |
| `syn insights overview`, `cost`, `heatmap [-d]` (calls `/insights/...`) | `cli/insights.ts` |
| `syn artifacts list -w`, `show`, `content` (no `--raw`) | `cli/artifacts.ts` |
| `syn execution sessions --all --json --kind --phase --attempt --limit --max-pages --cursor --require-complete --refresh --idempotency-key`; top-level `complete`, `coverage_complete`, `traversal_complete`, `pending_sections` | `cli/execution-sessions.ts`, `cli/execution-sessions-view.ts` |
| `syn execution transcript <execution-id> <harness> <native-id> <hash> --raw --json`; nonzero on `not_captured`, `missing`, `expired`, `deleted`, `too_large` | `cli/execution-transcript.ts` |
| `syn triggers register -r -w -e -c --max-attempts (5) --cooldown (300)`, sends no `input_mapping`, `daily_limit` 20; `enable <preset> -r [-w]`; `list -r -s -a`; `show`; `history -n`; `pause`, `resume` (no `--reason`); `delete -f`; `disable-all -r -f` | `cli/triggers.ts` |
| `syn github repos [-i] [--include-private]` | `cli/github.ts` |
| `syn repo list` | `cli/repo.ts` |
| `syn marketplace add <org/repo> -r/--ref (main) -n/--name`, `list` (Name, Repo, Ref, Added), `remove`, `refresh [name]`; `marketplace.json` required at the root; duplicate name refused | `cli/marketplace/registry.ts` |
| index cache four hours; failed index fetch returns null and is skipped | `apps/syn-cli-node/src/marketplace/client.ts` (`CACHE_TTL_MS`) |
| `marketplace.json`: `name`, optional `syntropic137 {type, min_platform_version}`, `plugins[]` with `name`, `source`, `version`, `description`, `category`, `tags`, `ref`; absolute or `..` source refused | `apps/syn-cli-node/src/marketplace/models.ts` |
| `syn workflow search [query] -c/--category -t/--tag -r/--registry`; `info <name>` first match | `cli/workflow/search.ts` |
| install: bare name tried in marketplaces; ref precedence; claude_plugins and skills preflight; non-transactional error; prune on newer version | `cli/workflow/install.ts` |
| package formats `workflows/*/workflow.yaml`, `workflow.yaml`, loose `*.yaml`; `shared://` to `phase-library/`; manifest `syntropic137-plugin.json` | `apps/syn-cli-node/src/packages/resolver.ts` |
| `syn workflow init [dir] -n -t --phases --multi` (phases/*.md, README.md; multi adds manifest and phase-library) | `cli/workflow/install.ts`, `apps/syn-cli-node/src/packages/resolver.ts` |
| `syn workflow export <id> -f/--format package\|plugin -o/--output DIR --force` | `cli/workflow/export.ts` |
| `syn workflow validate <file\|dir>` (file posted to `/workflows/validate`; directory resolved locally then each validated) | `cli/workflow/crud.ts` |
| a marketplace root (`marketplace.json` plus `plugins/<name>/workflow.yaml`) is not a package: `detectFormat` raises "No workflow files found"; the entry directory resolves as `single`; `info` prints `Source: <repo> (<source>)` | `apps/syn-cli-node/src/packages/resolver.ts`, `cli/workflow/search.ts`; fixture run through `detectFormat` on main |
| `syn workflow init` prompt template writes `max-tokens: 4096`; the scaffold fails `WorkflowDefinition.from_file` with `max_tokens is not supported` and passes once that line is removed (single and `--multi`) | `apps/syn-cli-node/src/packages/resolver.ts` (`PHASE_MD_TEMPLATE`); scaffold generated with `scaffoldSinglePackage` and `scaffoldMultiPackage` on main |
| `syn org create -n -s`, `list`, `show`, `update`, `delete -f` | `cli/org.ts` |
| `syn system create -n -d -o (required)`, `list -o`, `show`, `update`, `delete -f`, `status`, `cost`, `activity -n`, `patterns`, `history -n` | `cli/system.ts` |
| `syn repo register -u -o` (single org auto-selected; `--system` parsed and not sent), `list -o -s`, `show`, `assign -s`, `unassign`, `health`, `cost`, `activity`, `failures`, `sessions` | `cli/repo.ts` |

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
| `GET /executions/{id}/session-inventory`; `/{snapshot_id}/{kind}` with `limit` (up to 500), `cursor`, `phase_id`, `attempt_id`, `410 cursor_expired`; `/{snapshot_id}/nodes/{node_key}` | `api/routes/executions/inventory.py`, `inventory_cursor.py`, `inventory_summary.py` |
| `GET /executions/{id}/session-transcripts/{archive_sha256}?harness&native_id`; `status`, `content_format`, `size`, `content_base64`, `conversation` | `api/routes/executions/transcripts.py` |
| `GET /sessions` params `workflow_id`, `execution_id`, `status`, `statuses`, `started_after`, `started_before`, `q`, `page`, `page_size`; `parent_session_id`, `root_session_id`; `GET /sessions/{id}` `operations[]` with `tool_input`, `tool_output` | `api/routes/sessions.py`, `api/types.py` |
| `GET /observability/sessions/{id}/tools` (`executions[]`), `/tokens` (`input_tokens`, `output_tokens`, `total_tokens`, `cache_creation_tokens`, `cache_read_tokens`, `total_cost_usd`) | `api/routes/observability.py` |
| `GET /costs/sessions/{id}` (`cost_by_model`, `cost_by_tool`, `tokens_by_tool`, `unpriced_observation_count`, `unmeasured_fields`), `GET /costs/executions/{id}` (`cost_by_phase`, `unpriced_by_phase`, `is_complete`), `GET /costs/sessions`, `/costs/executions`, `/costs/summary`; `unattributed-model` key | `api/routes/costs.py` |
| `GET /metrics?workflow_id` | `api/routes/metrics.py` |
| `GET /insights/overview`, `/insights/cost`, `/insights/contribution-heatmap` | `api/routes/insights.py` |
| `POST /triggers` (`name`, `event`, `repository`, `workflow_id`, `conditions[]` with string `value`, `input_mapping`, `config` defaults 3 / 20 / 300); `POST /triggers/presets/{preset_name}` (duplicate name and event refused); `PATCH /triggers/{id}` `action` `pause`/`resume`, `reason`; `DELETE /triggers/{id}` | `api/routes/triggers/commands.py` |
| `GET /triggers?repository&status`, `GET /triggers/{id}` (`fire_count`, `conditions`, `input_mapping`, `config`, `last_fired_at`), `GET /triggers/{id}/history` (`entries[]`: `fired_at`, `execution_id`, `event_type`, `pr_number`, `status`, `cost_usd`, `guard_name`, `block_reason`) | `api/routes/triggers/queries.py` |
| `ExecutionDetailResponse.inputs` | `api/routes/executions/models.py` |
| `POST /workflows/validate` (`content`, `filename`; `valid`, `name`, `workflow_type`, `phase_count`, `errors`, `warnings`; no `prompt_file` base dir) | `api/routes/workflows/commands.py` |
| `GET /workflows/{id}/export?format=package\|plugin` | `api/routes/workflows/queries.py` |
| `/organizations` CRUD; `/systems` CRUD, `organization_id` filter, `/status`, `/cost`, `/activity`, `/patterns`, `/history` | `api/routes/organizations.py`, `api/routes/systems.py` |
| `/repos` CRUD, filters `organization_id`, `system_id`, `provider`, `unassigned`; `/assign` (`system_id`), `/unassign`, `/health`, `/cost`, `/activity`, `/failures`, `/sessions`; `DELETE` 409 with active triggers | `api/routes/repos.py` |
| no `/organizations/overview` | `api/routes/organizations.py`, `api/routes/insights.py` |

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
| unset codex model defaulted at install (`SYN_DEFAULT_CODEX_MODEL`) | `packages/syn-shared/src/syn_shared/agents.py`, `settings/config.py` |
| gap reasons; coverage states; settlement grace default 1800 s | `packages/syn-domain/.../agent_sessions/domain/services/gap_reasons.py`, `coverage_settlement.py`; `packages/syn-shared/src/syn_shared/settings/session_inventory.py` |
| webhook event matched as `<event>.<action>`, repository as `repository.full_name` | `api/routes/webhooks/handlers.py` |
| condition operators; `"true"`/`"false"` coerced; `in` takes a comma-separated string; dot paths with `[n]`; unresolved input paths dropped | `packages/syn-domain/.../github/slices/evaluate_webhook/condition_evaluator.py`, `aggregate_trigger/TriggerCondition.py` |
| guards `max_attempts`, `cooldown`, `daily_limit`, `idempotency`, `cross_trigger_cooldown` (window 0), `concurrency`, `dispatch_rate_limit`; no debouncer wired in production | `.../evaluate_webhook/safety_guards.py`, `EvaluateWebhookHandler.py`; `apps/syn-api/src/syn_api/_wiring.py` |
| presets `self-healing`, `review-fix`, `comment-command`: events, conditions, input mappings, limits, default workflow `self-heal-pr` | `packages/syn-domain/.../github/_shared/trigger_presets.py` |
| polled versus webhook-only events | `packages/syn-domain/.../github/_shared/event_availability.py` |
| an input named `repository` becomes the run's repository | `packages/syn-domain/.../github/slices/dispatch_triggered_workflow/projection.py` |
| every workflow, phase, input, agent and repository key; `extra="forbid"`; `max_tokens` rejected; `can_open_pr` retired; `execution_type` sequential only; `sandbox: read-only` refused; `claude-interactive` rejected; reserved input names; tool vocabulary and codex rule; `input_artifacts` resolution; `prompt_file` and frontmatter aliases | `packages/syn-domain/.../orchestration/_shared/workflow_definition.py` |
| `allowed_tools` under `agent:` rejected (`extra_forbidden`); the complete example valid | checked with `WorkflowDefinition.from_yaml` and `validate_workflow_yaml` on main |
| `requires_repos` default true | `packages/syn-domain/.../orchestration/_shared/yaml_to_command.py` (`infer_requires_repos`) |
| unknown `type` stored as `custom` | same file; `validate_workflow_yaml` returns valid for `type: bogus` |
| plugin refs `org/repo@v`, `<url>@v`; skill refs `org/repo/skill@v`; `@latest` rejected | `.../orchestration/_shared/claude_plugin_ref.py`, `skill_ref.py` |
| placeholders `{{execution_id}}`, `{{workflow_id}}`, `{{repo_url}}`, deprecated `{{repository}}`, inputs, `{{<phase-id>}}` and appendix cut to 2000, `$ARGUMENTS` from `task`; `{{repos}}` from `-R` | `apps/syn-api/src/syn_api/_wiring.py`; `WorkflowExecutionProcessor` |
| `task` from `-t`, else `-i task=`, else the declared `task` default; `-t` wins over `-i task=`; with no task `$ARGUMENTS` renders empty and `{{task}}` stays literal | `cli/workflow/run.ts` (sends `inputs` and `task`); `api/routes/executions/commands.py` (`_merge_inputs`); `_wiring.py` (`_substitute_inputs`), called directly on main |
| assign refused when already assigned; unassign refused when unassigned; duplicate registration refused | organization context repo aggregate; `api/routes/repos.py` (409) |
| no automatic repo registration from GitHub events | `POST /repos` is the only registration route; `syn repo register` its only caller |

## Harness discovery

See the pull request description for the exact commands and output used to
check that Claude Code and Codex both discover the migrated skills from a
local checkout.
