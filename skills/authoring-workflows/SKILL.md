---
name: authoring-workflows
description: Use when writing or changing a Syntropic137 workflow definition - the workflow YAML, its phases, phase prompts, declared inputs, the agent block (claude or codex), tool restrictions, prompt files and shared phase libraries, or scaffolding a new workflow package. Trigger phrases include "write a workflow", "write a workflow yaml", "create a workflow YAML", "add a phase", "workflow schema", "what keys does a phase take", "prompt_file", "prompt_template", "phase-library", "shared://", "$ARGUMENTS", "{{task}}", "{{repo_url}}", "pass output between phases", "declare a workflow input", "allowed_tools", "use codex for a phase", "requires_repos", "syn workflow init", "extra inputs are not permitted", "unknown tool". Do NOT use for running, registering or updating a workflow you already have (use syn-workflow), for browsing or publishing a marketplace (use workflow-marketplace), or for diagnosing a run that already started (use execution-control).
---

# Authoring Syntropic137 workflows

A workflow definition is a YAML document that names a workflow, declares the
inputs it takes, and lists ordered **phases**. Each phase is one headless
agent invocation with its own prompt, harness, model and tool set. Phases run
in order, and each later phase can read what earlier phases produced.

The schema is strict: an unknown key anywhere is a hard error, not a
warning. That is deliberate, because a misspelt key that loaded silently
would be a setting that never took effect. Most authoring failures are one of
three traps, summarised under Anti-patterns and explained in
[references/traps.md](references/traps.md).

## When to Use

- You are writing a new workflow definition or package, from scratch or from
  `syn workflow init`.
- You are adding or changing phases, prompts, declared inputs, the agent
  block or tool restrictions.
- Validation rejected a key ("extra inputs are not permitted", "unknown
  tool") and you need to know what the schema accepts.
- A run warned that a task or input would be discarded, and the fix is in the
  definition.

## When NOT to Use

- The definition is written and you want to register, update, run or archive
  it: use syn-workflow.
- You want a workflow someone else wrote, or to publish yours: use
  workflow-marketplace.
- A run has already started or failed: use execution-control.

## Input

- **Deployment** (required, environment): `SYN_API_URL`, default
  `http://localhost:8137`. Credentials are `SYN_API_TOKEN` (bearer) or
  `SYN_API_USER` + `SYN_API_PASSWORD` (basic). If `syn` is not installed:
  `npx @syntropic137/setup cli`. The schema is the deployment's: a key
  accepted by one version may be rejected or retired by another, so validate
  against the deployment you will register on.
- **Package directory** (path, required): where the definition lives, new or
  existing. `init` creates it.
- **What the workflow should do** (prose, required): the phases you need and
  what each one produces.
- **Whether it takes a task** (yes or no, required): decides whether a prompt
  must read `$ARGUMENTS`.
- **Whether it works on a repository** (yes or no, required): decides
  `requires_repos`.
- **Declared inputs** (optional): each with a name, description, whether it
  is required, and a string default.
- **Harness per phase** (optional): claude (the default) or codex.

## Workflow

1. Check which deployment will validate the definition, because validation
   runs on that deployment's schema:

   ```bash
   syn config show     # SYN_API_URL, and whether credentials are set
   syn health          # validation runs on this deployment's schema
   ```

2. Scaffold the package:

   ```bash
   syn workflow init ./pr-review --name "PR Review" --type review --phases 2
   syn workflow init ./my-flows --multi     # several workflows sharing a phase-library/
   ```

   `init` writes a `workflow.yaml`, one `phases/<id>.md` prompt file per phase
   referenced by `prompt_file`, and a `README.md`. `--multi` lays out
   `workflows/<name>/workflow.yaml` with a shared `phase-library/` and a
   `syntropic137-plugin.json` manifest.

3. Delete the `max-tokens: 4096` line from every generated prompt file (each
   `phases/*.md`, and `phase-library/*.md` with `--multi`) before you
   validate. The scaffold writes it into each file's frontmatter, it is read
   as `max_tokens`, and `max_tokens` is rejected, so an untouched scaffold
   fails validation:

   ```bash
   grep -rn '^max-tokens:' ./pr-review     # must print nothing before you validate
   ```

   The other generated frontmatter keys (`model`, `argument-hint`,
   `allowed-tools`, `timeout-seconds`) validate as written.

4. Write the workflow level: `id`, `name`, `phases` are required; `id` is the
   platform id, so reusing an existing id updates that workflow. Leave
   `requires_repos` unset for a workflow that works on a repository (it
   defaults to true) and set it to `false` only for work that needs no
   checkout. Every key is in [references/schema.md](references/schema.md).

5. Declare inputs. Each takes `name`, `description`, `required` (default
   true) and `default` (a string). Do not declare `repos` or `repository`:
   both are reserved, because repositories arrive with `-R`, not as inputs.

6. Write each phase: `id`, `name` and a unique `order` are required, plus
   exactly one of `prompt_template` (inline) or `prompt_file` (from a file).
   Put `allowed_tools` on the phase, not in its `agent:` block. Bound a phase
   with `timeout_seconds`. The phase key table is in
   [references/schema.md](references/schema.md).

7. Choose the harness per phase with the `agent` block, which takes only
   `provider` (`claude` by default, or `codex`), `model`, `sandbox` and
   `allow_delegation`. Omit the block for a claude phase on the default model.

8. Wire the prompts so everything the caller supplies reaches one:
   - the task as `$ARGUMENTS` (or `{{task}}`) in the first phase's prompt, if
     the workflow takes a task;
   - the repository as `{{repo_url}}`;
   - each declared input as `{{name}}`;
   - an earlier phase's output as `{{<phase-id>}}`, cut to 2000 characters,
     so ask that phase to end with a short summary.

   Prompt files (`phases/review.md`, `shared://create-pr`), their
   frontmatter, pinned `claude_plugins` and `skills`, and every placeholder
   are in [references/schema.md](references/schema.md).

9. Validate, then rehearse the install:

   ```bash
   syn workflow validate ./pr-review/workflow.yaml    # a self contained file
   syn workflow validate ./pr-review/                 # a package: resolves prompt_file, then validates
   syn workflow install ./pr-review/ --dry-run
   ```

   Read every warning. A definition that uses `prompt_file` must be
   registered as a package with `syn workflow install`, because
   `syn workflow create --from` sends one file and cannot resolve the
   references. Registering, updating and running are covered by syn-workflow.

## Output

- A package directory whose `workflow.yaml` (and any `phases/*.md` or
  `phase-library/*.md`) passes `syn workflow validate`, with every warning
  read.
- No `max-tokens:` line left in any prompt file.
- A `syn workflow install <dir> --dry-run` that succeeds, ready to hand to
  syn-workflow for registration.
- Nothing registered on the deployment yet: that is syn-workflow's step.

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

## Anti-patterns

- **A task workflow with no `$ARGUMENTS` in any prompt.** `-t` is then
  refused, because the task would be thrown away. Without `-t`, `-i task=` or
  a `default`, a workflow that does read the task still dispatches with
  `$ARGUMENTS` empty and `{{task}}` left as literal text. Trap 2 in
  [references/traps.md](references/traps.md).
- **`allowed_tools` inside the `agent:` block.** Rejected: it is a phase
  field. Names outside the closed set, or any non-empty list on a codex
  phase, are rejected too. Trap 3 in [references/traps.md](references/traps.md).
- **`requires_repos: false` on a workflow that needs a checkout.** `-R` is
  then not cloned and the CLI warns "the repos will not be cloned". Trap 1 in
  [references/traps.md](references/traps.md).
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

## Recommended tools and practices (as of 2026-10-04)

### Outcome: the definition validates on the deployment that will run it

- **`syn workflow validate` as the authority on the schema.** This skill and
  its references describe the schema; the deployment enforces it. Ladders up
  because a key accepted by one version may be rejected or retired by
  another, and only the target deployment can say which. Tradeoffs: it needs
  a reachable deployment.
- **Validate a package directory, not just its `workflow.yaml`.** Ladders up
  because the directory form resolves `prompt_file` before validating, so
  prompt-file frontmatter is checked too. The HTTP validate call in
  [references/http-api.md](references/http-api.md) cannot resolve
  `prompt_file`. Tradeoffs: none.
- **`syn workflow init --help` and `syn workflow validate --help`.** Ladders
  up by giving the full flag list of the installed CLI version, which can be
  newer than this skill.

### Outcome: everything the caller supplies reaches a prompt

- **`$ARGUMENTS` in the first phase's prompt, `{{name}}` for every declared
  input.** Ladders up because a task or input that no prompt reads is
  refused or discarded at run time. Tradeoffs: none.
- **`syn workflow run <id> ... --dry-run` with representative arguments
  after registering.** Ladders up by running the CLI's pre-dispatch checks
  (discarded task, discarded input, uncloned repos) without spending a run.
  Tradeoffs: it needs the workflow registered first (see syn-workflow).

### Outcome: the template is reusable

- **Prompt files over long inline strings.** A package with `phases/*.md`
  diffs, reviews and reuses better than a YAML string, and `shared://`
  shares one prompt across workflows. Ladders up by keeping prompts editable
  without touching the schema. Tradeoffs: the package must be registered
  with `syn workflow install`, not `create --from`.
- **Claude Code's own documentation on skills and slash commands, for claude
  phase prompts.** A claude phase prompt can invoke installed slash commands
  and skills. A codex phase cannot invoke slash commands or Claude plugins,
  so write its prompt as plain instructions; skills installed for it are
  usable. Ladders up by reusing tested commands instead of restating them in
  every prompt.

## References

- [references/schema.md](references/schema.md): every key at the workflow,
  input, phase and agent levels, prompt-file resolution, pinned plugins and
  skills, and the placeholder table. Read while writing the definition.
- [references/traps.md](references/traps.md): the three traps
  (`requires_repos`, `$ARGUMENTS`, `allowed_tools`) in full. Read when a run
  warns about discarded or uncloned values, or `allowed_tools` is rejected.
- [references/example.md](references/example.md): a complete two-phase
  definition with what each choice shows. Read for a shape to copy.
- [references/http-api.md](references/http-api.md): validating a single file
  over HTTP. Read when you need structured output or the CLI is unavailable.

## Continual improvement

File drift, gaps, or proposed updates at
https://github.com/syntropic137/syntropic137-skills/issues
