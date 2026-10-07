---
name: syn-workflow
description: Use when operating Syntropic137 workflow templates through the `syn` CLI - finding which workflows a deployment can run, reading a workflow's phases and declared inputs, starting a run with the right task, inputs and repositories, validating a workflow YAML or package, registering or updating a workflow, archiving one, or listing a workflow's past runs. Trigger phrases include "run a workflow", "start a syn workflow", "write the task", "rewrite the task after execution-control traced a first-phase timeout to its scope", "what workflows are installed", "what inputs does this workflow take", "register this workflow", "install a workflow package", "update the workflow in place", "refusing to overwrite recorded provenance", "is already installed", "task would be discarded", "delete a workflow", "syn workflow". Do NOT use for watching, cancelling, resuming or diagnosing an execution that has already started (use execution-control), for designing or writing a workflow's YAML, phases or prompts (use authoring-workflows), for browsing, installing from or publishing to a marketplace (use workflow-marketplace), or for reviewing what a batch of finished runs teaches (use mining-session-logs).
---

# Operating Syntropic137 workflows

A workflow is a template registered in a Syntropic137 deployment: an id, a
name, an ordered list of phases (each one headless agent invocation with its
own prompt and model), and a set of declared inputs. Running a workflow
creates an **execution** with its own `exec-...` id.

The expensive mistake here is not a failed command. It is a run that starts,
spends full money and time, reports success, and did work nobody asked for
because the task or an input never reached a prompt. Almost everything below
exists to make that impossible.

## When to Use

- You need to know which workflows a deployment can run, or what inputs one
  takes.
- You are about to start a run and want the task, inputs and repositories to
  reach the prompts.
- You are registering, updating, archiving or uninstalling a workflow.
- You want the list of past runs of one workflow.

## When NOT to Use

- The run has already started and you need to follow, cancel, resume or
  diagnose it: use execution-control.
- You are writing the workflow YAML itself: use authoring-workflows.
- You are browsing, searching or publishing to a marketplace: use
  workflow-marketplace.
- You want lessons from a batch of finished runs: use mining-session-logs.

## Input

- **Deployment** (required, environment): `SYN_API_URL`, default
  `http://localhost:8137`. Credentials are `SYN_API_TOKEN` (bearer) or
  `SYN_API_USER` + `SYN_API_PASSWORD` (basic). If `syn` is not installed:
  `npx @syntropic137/setup cli`.
- **Workflow id** (string, required to run or show): a unique prefix is
  accepted by `syn workflow show`.
- **Task** (string, optional): `-t`, `--task`. Phase prompts read it as
  `$ARGUMENTS` or `{{task}}`.
- **Inputs** (`key=value`, optional, repeatable): `-i`, `--input`, any other
  declared input.
- **Repositories** (optional, repeatable): `-R`, `--repo`, as `owner/repo`, a
  full GitHub URL, or a `repo-...` id from `syn repo list`. Repositories are
  not inputs: `repos` and `repository` are rejected as `--input` keys.
- **Run modifiers** (optional): `-n`, `--dry-run` checks everything and
  dispatches nothing; `-q`, `--quiet` skips the run preview.
- **Definition** (required to register): a self-contained `.yaml` file, a package
  directory, a git URL, `org/repo`, or a marketplace name.

## Workflow

1. Check which deployment you are talking to, because the same workflow id can
   resolve to different definitions on different hosts:

   ```bash
   syn config show     # SYN_API_URL, and whether credentials are set
   syn health          # is that deployment reachable and healthy
   ```

2. Find the workflow:

   ```bash
   syn workflow list                     # registered on this deployment, runnable
   syn workflow list --include-archived  # also archived (deleted) templates
   syn workflow packages                 # packages this machine installed, with version and source
   ```

   `syn workflow list` prints ONE page of `GET /workflows` and does not
   paginate. Before concluding a workflow is absent, try
   `syn workflow show <workflow-id>`, or page the HTTP endpoint (see
   [references/http-api.md](references/http-api.md)) until a page comes back
   short. `packages` reads local install history (under
   `~/.syntropic137/workflows/`, or `$SYN_CONFIG_DIR`), not the deployment, so
   a package can be listed there and missing from the deployment, or the
   reverse.

3. Read what it needs with `syn workflow show <workflow-id>`. It prints the
   id, name, type, classification, each phase with its model, and each
   declared input marked `[required]` or `[optional]`, with its description
   and default. An input that is required and has no default must be
   supplied.

4. Write the task so a phase can finish it and a reader can check it. Name
   the trap a previous run hit and the command that proves it was avoided;
   keep anything asked of a premise or check phase read-only; scope it to
   what one phase can finish, splitting an "every X" task into batches;
   require pasted command output, not summaries; check the repository's
   existing designs before asking for one; pass with `-R` every repository
   the change may touch; paste in any deployment data the run needs, since
   a phase cannot query the deployment. Each rule, with what was
   observed when it was broken, is in
   [references/writing-tasks.md](references/writing-tasks.md).

5. Rehearse the run whenever the inputs are not obviously right. `--dry-run`
   runs every local check in step 6 and stops before anything is dispatched:

   ```bash
   syn workflow run <workflow-id> -t "Fix the auth timeout" -R owner/repo --dry-run
   ```

6. Run it, and read every warning, because the CLI warns only when something
   you typed will not reach the agent:

   ```bash
   syn workflow run <workflow-id> -t "Fix the auth timeout" -R owner/repo
   syn workflow run <workflow-id> -t "Review PR 42" -R owner/repo -i base_branch=develop
   syn run <workflow-id> -t "Implement retry logic"   # shortcut for `syn workflow run`
   ```

   | situation | result |
   |---|---|
   | a required input with no default is missing | error, nothing runs |
   | `-i repos=...` or `-i repository=...` | error: use `-R` |
   | `-t` given, but no phase prompt consumes the task | **error**: the task would be discarded |
   | a phase consumes the task, none supplied, no default | warning: it will render empty |
   | an `--input` no phase prompt references | warning: it will be discarded |
   | `-R` given, but the workflow does not clone repos | warning: the repos will not be cloned |

   On success it prints `Execution ID: exec-...` and the deployment it ran
   on. From here the run belongs to execution-control. Take the id from
   that line, or from `syn execution list`, never by matching `exec-`
   anywhere in the output: the output echoes the task, and a task that
   mentions another execution's id yields the wrong one.

   A start refused with HTTP 507 and "Refusing to start a new execution: the
   workspace volume is nearly full" is the deployment's disk, not the
   workflow or the task. Retrying does not help until space is freed; tell
   whoever operates the deployment.

7. To see a workflow's past runs, use `syn workflow status <workflow-id>`. It
   takes a workflow id, not an execution id.

8. To register a definition, validate it with
   `syn workflow validate ./my-workflow.yaml` (a single file) or
   `syn workflow validate ./my-package/` (a package directory), then register
   it by what you have:

   | you have | register with |
   |---|---|
   | one self-contained YAML file | `syn workflow create "<name>" --from ./my-workflow.yaml` |
   | a package directory, or phases that use `prompt_file` | `syn workflow install ./my-package/` |
   | a git URL, `org/repo`, or a marketplace name | `syn workflow install <source>` (add `--ref <branch-or-tag>` to pin; default `main`) |

   The YAML `id` is the platform id, so registering a definition whose id
   already exists updates that workflow instead of creating a second one.
   Flag details for `create` and `install` are in
   [references/registering-and-updating.md](references/registering-and-updating.md).

9. To update a workflow in place, re-register it the same way it was first
   registered, because `create --from` and `install` record different
   provenance:
   - first registered with `create --from`: re-run the same `create --from`;
   - first registered with `install` from a directory: bump `version` in the
     package manifest (`syntropic137-plugin.json`) and re-run
     `syn workflow install <dir>`, or re-run it with `--force` to overwrite
     the same version;
   - first installed from git or a marketplace:
     `syn workflow update <package-name>` (accepts `--ref`, `--dry-run`,
     `--force`).

   If a refusal comes back, look it up in
   [references/registering-and-updating.md](references/registering-and-updating.md)
   before reaching for `--force`.

10. To archive or remove:

   ```bash
   syn workflow delete <workflow-id> --force          # archive (soft delete)
   syn workflow uninstall <package-name>               # remove an installed package and archive its workflows
   syn workflow uninstall <package-name> --keep-workflows
   ```

   `delete` refuses without `--force`. Archived workflows stay visible with
   `syn workflow list --include-archived`, and reinstalling one restores it.

## Output

- After a run: the `exec-...` execution id and the deployment it ran on,
  reported to the caller, plus every warning the CLI printed and whether it
  was accepted on purpose.
- After a dry run: the preview and check results; nothing dispatched.
- After registering or updating: the workflow id, unchanged for an update.
- After deleting or uninstalling: the workflow archived, visible under
  `--include-archived`, and restorable by reinstalling.

## Outcomes we are looking for

### Outcome 1: the run that starts is the run that was asked for

- *Signal:* before running, the caller has read the workflow's declared inputs
  and knows which ones are required, which have defaults, and whether a phase
  consumes the task.
- *Signal:* the run command produced no warnings, or each warning was read
  and accepted on purpose.
- *Signal:* the task names the check that proves it was done, asks for
  pasted output, and fits in one phase.

### Outcome 2: a changed workflow updates in place

- *Signal:* re-registering a workflow uses the same path it was first
  registered with, and the workflow id does not change.
- *Signal:* a provenance refusal is answered by registering the right way,
  never by forcing past it or editing fields the schema rejects.

### Outcome 3: nothing is lost by accident

- *Signal:* deleting a workflow is understood as archiving it, done with an
  explicit confirmation, and reversible by reinstalling.

## Anti-patterns

- **Passing `-t` to a workflow whose prompts never read it.** The CLI refuses
  this: the task would be discarded and the workflow would run its own
  hardcoded prompt instead. Drop `-t`, or pick the workflow that takes a task.
- **Ignoring "will be discarded".** An `--input` that no phase prompt
  references is dropped silently on the platform side. The warning is the
  only notice you get.
- **Treating `syn workflow list` and `syn workflow packages` as the same
  list.** One is what the deployment can run; the other is what this machine
  installed.
- **Passing an execution id to `syn workflow status`.** It takes a workflow
  id and lists that workflow's runs. For one execution, use
  `syn execution show <execution-id>` (see execution-control).
- **Opening a task with build or test steps.** Observed 2026-10-04..06:
  the first phase, meant to check the premise, did the implementation work
  instead and timed out.
- **"Every X" in one task.** It grows past one phase's timeout, and a resume
  replays it unchanged. Split it into batches.
- **Accepting "tests pass" as evidence.** Ask for the pasted output.
- **Briefing a design without reading the designs already written.**
  Observed 2026-10-07: three such tasks were refused at premise in one day.
- **Passing only the repository the change starts in.** The workspace
  credential covers only `-R` repositories; a fix that needs another one
  dead-ends.
- **Asking a run to look up deployment data.** A phase has no route to the
  deployment's API. Measure first and paste the data into the task.
- **Answering a provenance refusal with `--force`.** It does not bypass that
  refusal, and the refusal is correct.

## Recommended tools and practices (as of 2026-10-07)

### Outcome: the run that starts is the run that was asked for

- **`syn workflow show` before every unfamiliar run.** Ladders up by putting
  the declared inputs, their defaults and the phases in front of the caller
  before any money is spent. Tradeoffs: one extra call; it is cheap and a
  misdirected run is not.
- **`syn workflow run ... --dry-run`.** Ladders up by running the
  pre-dispatch checks (discarded task, discarded input, uncloned repos)
  without dispatching. Tradeoffs: none beyond the call.
- **The CLI over a direct `POST /workflows/{id}/execute`.** Ladders up
  because the HTTP path skips the CLI's pre-dispatch checks, so a direct
  `POST` will start a run whose task or inputs are discarded without warning.
  Tradeoffs: when structured output is needed, use the HTTP surface in
  [references/http-api.md](references/http-api.md), after a dry run.
- **The task-writing rules in
  [references/writing-tasks.md](references/writing-tasks.md).** Ladders up
  because a task that names its trap and its proving command, stays inside
  one phase, asks for pasted output, declares every repository it may touch
  and carries the deployment data it needs is the cheapest fix for a run that
  failed for task reasons. Tradeoffs: a longer task; it is cheaper than a
  second run.
- **`syn workflow list` to find what the deployment can run, not
  `syn workflow search` or `syn workflow info`.** Ladders up because those two
  search configured marketplaces, not the deployment.

### Outcome: a changed workflow updates in place

- **The registration-path table in step 8 and the refusal table in
  [references/registering-and-updating.md](references/registering-and-updating.md).**
  Ladders up by mapping each refusal message to the registration path that
  answers it. Tradeoffs: the refusal texts are matched on substrings and will
  drift with the CLI; `syn workflow <subcommand> --help` is authoritative for
  the installed version.

### Outcome: nothing is lost by accident

- **`syn workflow delete --force` as the only delete path.** Ladders up
  because the explicit `--force` is the confirmation, and the result is an
  archive, not an erasure. **`uninstall --keep-workflows`** keeps the
  registered workflows when only the local package should go.

## References

- [references/writing-tasks.md](references/writing-tasks.md): the
  task-writing rules with what was observed when each was broken. Read
  before writing a task for a multi-phase workflow, or re-running one that
  failed.
- [references/registering-and-updating.md](references/registering-and-updating.md):
  `create` and `install` flags, and every provenance refusal with what it
  means. Read when registering or when an update is refused.
- [references/http-api.md](references/http-api.md): the HTTP endpoints behind
  the CLI, with query parameters and request bodies. Read when you need
  structured output or the CLI is unavailable.

## Continual improvement

File drift, gaps, or proposed updates at
https://github.com/syntropic137/syntropic137-skills/issues
