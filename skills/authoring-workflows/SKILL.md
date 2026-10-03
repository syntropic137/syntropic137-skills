---
name: authoring-workflows
description: Use when writing or changing a Syntropic137 workflow definition - the workflow YAML, its phases, phase prompts, declared inputs, the agent block (claude or codex), tool restrictions, prompt files and shared phase libraries, or scaffolding a new workflow package. Trigger phrases include "write a workflow", "create a workflow YAML", "add a phase", "workflow schema", "what keys does a phase take", "prompt_file", "prompt_template", "phase-library", "shared://", "$ARGUMENTS", "{{task}}", "{{repo_url}}", "pass output between phases", "declare a workflow input", "allowed_tools", "use codex for a phase", "requires_repos", "syn workflow init", "extra inputs are not permitted", "unknown tool". Do NOT use for running, registering or updating a workflow you already have (use syn-workflow), for browsing or publishing a marketplace (use workflow-marketplace), or for diagnosing a run that already started (use execution-control).
---

# Authoring Syntropic137 workflows

A workflow definition is a YAML document that names a workflow, declares the
inputs it takes, and lists ordered **phases**. Each phase is one headless
agent invocation with its own prompt, harness, model and tool set. Phases run
in order, and each later phase can read what earlier phases produced.

The schema is strict: an unknown key anywhere is a hard error, not a
warning. That is deliberate, because a misspelt key that loaded silently
would be a setting that never took effect. Most authoring failures are one of
a small set of traps listed below.

## Outcomes we are looking for

### Outcome 1: the definition validates on the deployment that will run it

- *Signal:* `syn workflow validate` on the file or package returns valid,
  with every warning read.

### Outcome 2: everything the caller supplies reaches a prompt

- *Signal:* if the workflow takes a task, some phase prompt contains
  `$ARGUMENTS` or `{{task}}`. Every declared input is referenced as
  `{{name}}` in some phase prompt.
- *Signal:* `syn workflow run <id> ... --dry-run` with representative
  arguments prints no "discarded" warning or refusal.

### Outcome 3: the template is reusable

- *Signal:* no task text and no repository name is hardcoded in a prompt.
  The task arrives as `$ARGUMENTS`, the repository as `{{repo_url}}`.

## Before you start

```bash
syn config show     # SYN_API_URL, and whether credentials are set
syn health          # validation runs on this deployment's schema
```

`SYN_API_URL` defaults to `http://localhost:8137`. Credentials are
`SYN_API_TOKEN` (bearer) or `SYN_API_USER` + `SYN_API_PASSWORD` (basic). If
`syn` is not installed: `npx @syntropic137/setup cli`.

The schema is the deployment's. A key accepted by one version may be
rejected or retired by another, so validate against the deployment you will
register on.

## Principles

- **Validate, do not guess.** `syn workflow validate` is the authority on
  the schema. This skill describes it; the deployment enforces it.
- **The task and the repository are parameters.** Prompts read the task as
  `$ARGUMENTS` and the repository as `{{repo_url}}`, so one template serves
  every task and repo.
- **Settings live where the schema puts them.** Tool restrictions are a
  phase setting. Harness, model and sandbox are agent settings. Putting one in
  the other's block is an error.
- **Prefer prompt files for anything long.** A package with `phases/*.md`
  diffs, reviews and reuses better than a YAML string.

## The traps

These three account for most definitions that validate but do not do what
the author meant, or do not validate at all.

### Trap 1: `requires_repos` and `-R`

`requires_repos` defaults to **true** when omitted. A workflow that works on
a repository needs no setting; the caller passes the repository at run time
with `-R owner/repo`, and phases read it as `{{repo_url}}`.

Set `requires_repos: false` only for work that needs no checkout (research,
summarising a URL). Then `-R` is not cloned: the CLI warns "the repos will
not be cloned" and the repository is never checked out.

Repositories are never inputs. Do not declare an input named `repos` or
`repository`: both names are reserved and the definition is rejected.

### Trap 2: `$ARGUMENTS` is the task, from `-t` or `-i task=`

`$ARGUMENTS` and `{{task}}` both render the task. The caller supplies it with
`-t/--task` (preferred) or `-i task=value`; if both are passed, `-t` wins. A
`default` on a declared input named `task` fills it when neither is passed.
Nothing else does: not another input, not a positional argument.

- A workflow whose prompts never mention `$ARGUMENTS` or `{{task}}` does not
  take a task. `syn workflow run ... -t "..."` is then **refused**, because the
  task would be thrown away.
- A workflow that consumes the task but is run without one (no `-t`, no
  `-i task=`, no `default`) still dispatches; the CLI warns. `$ARGUMENTS`
  renders empty and `{{task}}` is left in the prompt as literal text.

If the workflow is meant to take a task, put `$ARGUMENTS` in the first
phase's prompt.

### Trap 3: `allowed_tools` is a PHASE field, not an `agent:` field

```yaml
# WRONG: rejected, the agent block has no allowed_tools key
- id: review
  agent:
    provider: claude
    allowed_tools: [Read, Grep]

# RIGHT
- id: review
  allowed_tools: [Read, Grep, Glob]
  agent:
    provider: claude
```

The names come from a closed, case insensitive set: `Bash`, `Edit`, `Glob`,
`Grep`, `Read`, `Skill`, `Task`, `WebFetch`, `WebSearch`, `Write`. Any other
name is rejected. On a claude phase the list is the set of tools the agent
has; omit the key to keep every tool. On a codex phase a non-empty list is
rejected, because codex has no tool vocabulary. A list that keeps `Bash`
still gives the agent broad reach through the shell.

## Anti-patterns

- **Hardcoding the task or repo in a prompt.** The workflow then does one
  thing forever, and `-t` is refused.
- **Declaring an input no prompt references.** Values passed for it are
  discarded, with only a CLI warning to show for it.
- **Using `max_tokens` to bound a phase.** It is rejected; bound a phase
  with `timeout_seconds`.
- **Adding `can_open_pr`.** It is retired: accepted, dropped, and reported
  as a notice. It controls nothing.
- **Writing `sandbox: read-only`.** It is refused at authoring. Use
  `workspace-write` to keep a codex phase inside its workspace.

## The procedure

### 1. Scaffold

```bash
syn workflow init ./pr-review --name "PR Review" --type review --phases 2
syn workflow init ./my-flows --multi     # several workflows sharing a phase-library/
```

`init` writes a `workflow.yaml`, one `phases/<id>.md` prompt file per phase
referenced by `prompt_file`, and a `README.md`. `--multi` lays out
`workflows/<name>/workflow.yaml` with a shared `phase-library/` and a
`syntropic137-plugin.json` manifest.

**Delete the `max-tokens: 4096` line from every generated prompt file**
(each `phases/*.md`, and `phase-library/*.md` with `--multi`) before you
validate. The scaffold writes it into each file's frontmatter, it is read as
`max_tokens`, and `max_tokens` is rejected, so an untouched scaffold fails
validation:

```bash
grep -rn '^max-tokens:' ./pr-review     # must print nothing before you validate
```

The other generated frontmatter keys (`model`, `argument-hint`,
`allowed-tools`, `timeout-seconds`) validate as written.

### 2. Write the workflow level

| key | required | notes |
|---|---|---|
| `id` | yes | 1 to 100 characters. The platform id: registering a definition with an existing id updates that workflow |
| `name` | yes | |
| `description` | no | |
| `type` | no | `research`, `planning`, `implementation`, `review`, `deployment` or `custom` (default). Any other value is stored as `custom` without an error |
| `classification` | no | `simple`, `standard` (default), `complex` or `epic` |
| `requires_repos` | no | see Trap 1. Default true |
| `repository` | no | a default repository: `url` (required), `ref` (default `main`) |
| `repos` | no | a list of default repository URLs |
| `project_name` | no | |
| `inputs` | no | see step 3 |
| `phases` | yes | at least one; ids unique, orders unique |
| `claude_plugins`, `skills` | no | applied to every phase; see step 6 |

### 3. Declare inputs

```yaml
inputs:
  - name: task
    description: What to review
    required: true
  - name: base_branch
    description: Branch to compare against
    required: false
    default: main
```

Each input takes `name`, `description`, `required` (default true) and
`default` (a string). Callers pass inputs with `-i name=value`; `task` is
usually passed with `-t`, which wins over `-i task=`. Reference each input in
a prompt as `{{name}}`.

### 4. Write each phase

| key | notes |
|---|---|
| `id` | required. Letters, digits, `.`, `_`, `-`, starting with a letter or digit; up to 100 characters |
| `name` | required |
| `order` | required, 1 or more, unique |
| `description` | |
| `prompt_template` | the prompt inline |
| `prompt_file` | the prompt from a file; at most one of the two. A phase with neither has no instructions |
| `execution_type` | `sequential` only (the default). `parallel` and `human_in_loop` are rejected |
| `input_artifacts`, `output_artifacts` | named artifacts; each input must be an earlier phase's output or a workflow input name |
| `timeout_seconds` | |
| `allowed_tools` | see Trap 3 |
| `model` | wins over `agent.model` |
| `agent` | see step 5 |
| `clone_repos` | default true. `false` keeps the repository token and `{{repo_url}}` and skips only the checkout |
| `delivers_repo_changes` | default true |
| `argument_hint` | a hint for the task text this phase expects |
| `claude_plugins`, `skills` | applied to this phase only |

Rejected keys: `max_tokens` (use `timeout_seconds`), and any key not listed.
`can_open_pr` is accepted and dropped with a notice.

### 5. Choose the harness

```yaml
agent:
  provider: codex              # claude (default) or codex
  model: <a concrete model id>
  sandbox: workspace-write     # codex only: workspace-write or full-access (the default)
  allow_delegation: false
```

The `agent` block takes only `provider`, `model`, `sandbox` and
`allow_delegation`. Omit it for a claude phase on the default model.
`provider: claude-interactive` is rejected. Claude ignores `sandbox`.

### 6. Reference prompt files, plugins and skills

- `prompt_file: phases/review.md` resolves relative to the workflow's
  directory and may not escape the package.
- `prompt_file: shared://create-pr` resolves to `phase-library/create-pr.md`
  at the package root.
- A prompt file may start with frontmatter. `model`, `description`,
  `argument-hint`, `allowed-tools`, `execution-type` and `timeout-seconds`
  there are merged into the phase; a value set in the YAML wins.
- `claude_plugins` and `skills` entries are pinned references:
  `"org/repo@v1.2.0"` or `"<git-url>@v1.2.0"` for plugins, and
  `"org/repo/skill-name@v1.2.0"` or `"<git-url>@v1.2.0"` for skills. `@latest`
  is rejected: pin a tag, branch or commit.

A definition that uses `prompt_file` must be registered as a package with
`syn workflow install`, because `syn workflow create --from` sends one file and
cannot resolve the references (see syn-workflow).

### 7. Pass work between phases

| placeholder | renders |
|---|---|
| `$ARGUMENTS`, `{{task}}` | the task from `-t`, or `-i task=` when `-t` is absent |
| `{{name}}` | the declared input `name` |
| `{{repo_url}}` | the HTTPS URL of the repository |
| `{{repos}}` | every `-R` repository, as comma separated HTTPS URLs |
| `{{execution_id}}`, `{{workflow_id}}` | this run's ids |
| `{{<phase-id>}}` | an earlier phase's output, cut to 2000 characters |

Every phase after the first also receives the earlier phases' outputs (each
cut to 2000 characters) appended after its prompt. Ask a phase to end with a
short summary when a later phase depends on it. `{{repository}}` still
renders `owner/repo` but is deprecated: use `{{repo_url}}`.

### 8. Validate, then register

```bash
syn workflow validate ./pr-review/workflow.yaml    # a self contained file
syn workflow validate ./pr-review/                 # a package: resolves prompt_file, then validates
syn workflow install ./pr-review/ --dry-run
```

Registering, updating and running are covered by syn-workflow.

## A complete example

```yaml
id: pr-review
name: PR Review
description: Reviews a change and writes a findings report
type: review
classification: standard
inputs:
  - name: task
    description: What to review, for example "PR 42"
    required: true
  - name: focus
    description: Area to weight most heavily
    required: false
    default: correctness
phases:
  - id: investigate
    name: Investigate
    order: 1
    allowed_tools: [Read, Grep, Glob, Bash]
    timeout_seconds: 900
    output_artifacts: [notes]
    prompt_template: |
      In {{repo_url}}, review: $ARGUMENTS
      Weight {{focus}} most heavily. End with a five line summary.
  - id: report
    name: Report
    order: 2
    input_artifacts: [notes]
    output_artifacts: [report]
    agent:
      provider: codex
      sandbox: workspace-write
    prompt_template: |
      Using these notes, write the final review:
      {{investigate}}
```

Run with `syn workflow run pr-review -t "PR 42" -R owner/repo -i focus=security`.

## Recommended tools and practices (as of 2026-10-03)

Validate one self contained file over HTTP:

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
curl -sf -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$SYN_API_URL/api/v1/workflows/validate" \
  -d "$(jq -n --rawfile c workflow.yaml '{content: $c, filename: "workflow.yaml"}')"
```

The response has `valid`, `name`, `workflow_type`, `phase_count`, `errors`
and `warnings`. It cannot resolve `prompt_file`; validate packages with the
CLI.

For writing the phase prompts of a claude phase, Claude Code's own
documentation on skills and slash commands applies: a claude phase prompt can
invoke installed slash commands and skills. A codex phase cannot invoke slash
commands or Claude plugins, so write its prompt as plain instructions; skills
installed for it are usable.

Run `syn workflow init --help` and `syn workflow validate --help` for the full
flag list of the installed CLI version.
