---
name: syn-workflow
description: Use when operating Syntropic137 workflow templates through the `syn` CLI - finding which workflows a deployment can run, reading a workflow's phases and declared inputs, starting a run with the right task, inputs and repositories, validating a workflow YAML or package, registering or updating a workflow, archiving one, or listing a workflow's past runs. Trigger phrases include "run a workflow", "start a syn workflow", "what workflows are installed", "what inputs does this workflow take", "register this workflow", "install a workflow package", "update the workflow in place", "refusing to overwrite recorded provenance", "is already installed", "task would be discarded", "delete a workflow", "syn workflow". Do NOT use for watching, cancelling, resuming or diagnosing an execution that has already started (use execution-control), for designing a workflow's YAML from scratch, for browsing or publishing to a marketplace, or for reviewing what a batch of finished runs teaches (use mining-session-logs).
---

# Operating Syntropic137 workflows

A workflow is a template registered in a Syntropic137 deployment: an id, a
name, an ordered list of phases (each one headless agent invocation with its
own prompt and model), and a set of declared inputs. Running a workflow
creates an **execution** with its own `exec-...` id. This skill covers the
template side: finding one, understanding what it needs, starting it
correctly, and registering or changing it.

The expensive mistake here is not a failed command. It is a run that starts,
spends full money and time, reports success, and did work nobody asked for
because the task or an input never reached a prompt. Almost everything below
exists to make that impossible.

## Outcomes we are looking for

### Outcome 1: the run that starts is the run that was asked for

- *Signal:* before running, the caller has read the workflow's declared inputs
  and knows which ones are required, which have defaults, and whether a phase
  consumes the task.
- *Signal:* the run command produced no warnings, or each warning was read
  and accepted on purpose.
- *Signal:* the caller reports the execution id it got back, and the
  deployment it ran on.

### Outcome 2: a changed workflow updates in place

- *Signal:* re-registering a workflow uses the same path it was first
  registered with, and the workflow id does not change.
- *Signal:* a provenance refusal is answered by registering the right way,
  never by forcing past it or editing fields the schema rejects.

### Outcome 3: nothing is lost by accident

- *Signal:* deleting a workflow is understood as archiving it, done with an
  explicit confirmation, and reversible by reinstalling.

## Before you start

Every command talks to one deployment over HTTP. Check which one before
acting, because the same workflow id can resolve to different definitions on
different hosts:

```bash
syn config show     # SYN_API_URL, and whether credentials are set
syn health          # is that deployment reachable and healthy
```

`SYN_API_URL` defaults to `http://localhost:8137`. Credentials are
`SYN_API_TOKEN` (bearer) or `SYN_API_USER` + `SYN_API_PASSWORD` (basic). If
`syn` is not installed: `npx @syntropic137/setup cli`.

## Principles

- **Read before you run.** `syn workflow show <id>` is cheap; a misdirected
  run is not.
- **Repositories are not inputs.** They travel on `-R`. `repos` and
  `repository` are rejected as `--input` keys.
- **The YAML `id` is the platform id.** Registering a definition whose id
  already exists updates that workflow; it does not create a second one.
- **Register the way it was first registered.** `create --from` and
  `install` record different provenance and are not interchangeable for
  updates.
- **Warnings are findings.** The CLI warns only when something you typed will
  not reach the agent.

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
- **Answering a provenance refusal with `--force`.** It does not bypass that
  refusal, and the refusal is correct.

## The procedure

### 1. Find the workflow

```bash
syn workflow list                     # registered on this deployment, runnable
syn workflow list --include-archived  # also archived (deleted) templates
syn workflow packages                 # packages this machine installed, with version and source
```

`packages` reads local install history (under `~/.syntropic137/workflows/`,
or `$SYN_CONFIG_DIR`), not the deployment. A package can be listed there and
missing from the deployment, or the reverse.

### 2. Read what it needs

```bash
syn workflow show <workflow-id>       # a unique prefix of the id is accepted
```

This prints the id, name, type, classification, each phase with its model,
and each declared input marked `[required]` or `[optional]`, with its
description and default. An input that is required and has no default must
be supplied.

### 3. Rehearse the run

```bash
syn workflow run <workflow-id> -t "Fix the auth timeout" -R owner/repo --dry-run
```

`--dry-run` (`-n`) runs every local check below and stops before anything is
dispatched. Use it whenever the inputs are not obviously right.

### 4. Run it

```bash
syn workflow run <workflow-id> -t "Fix the auth timeout" -R owner/repo
syn workflow run <workflow-id> -t "Review PR 42" -R owner/repo -i base_branch=develop
syn run <workflow-id> -t "Implement retry logic"   # shortcut for `syn workflow run`
```

| flag | supplies |
|---|---|
| `-t`, `--task` | the task, which phase prompts read as `$ARGUMENTS` or `{{task}}` |
| `-i`, `--input key=value` | any other declared input; repeatable |
| `-R`, `--repo` | a repository; repeatable; `owner/repo`, a full GitHub URL, or a `repo-...` id from `syn repo list` |
| `-n`, `--dry-run` | check everything, dispatch nothing |
| `-q`, `--quiet` | skip the run preview |

What the CLI checks before dispatching, and what each outcome means:

| situation | result |
|---|---|
| a required input with no default is missing | error, nothing runs |
| `-i repos=...` or `-i repository=...` | error: use `-R` |
| `-t` given, but no phase prompt consumes the task | **error**: the task would be discarded |
| a phase consumes the task, none supplied, no default | warning: it will render empty |
| an `--input` no phase prompt references | warning: it will be discarded |
| `-R` given, but the workflow does not clone repos | warning: the repos will not be cloned |

On success it prints `Execution ID: exec-...` and the deployment it ran on.
From here the run belongs to execution-control.

### 5. Look at a workflow's past runs

```bash
syn workflow status <workflow-id>     # run history for this workflow
```

### 6. Validate and register a definition

```bash
syn workflow validate ./my-workflow.yaml     # a single file
syn workflow validate ./my-package/          # a package directory
```

Then register it, choosing the path by what you have:

| you have | register with |
|---|---|
| one self-contained YAML file | `syn workflow create "<name>" --from ./my-workflow.yaml` |
| a package directory, or phases that use `prompt_file` | `syn workflow install ./my-package/` |
| a git URL, `org/repo`, or a marketplace name | `syn workflow install <source>` (add `--ref <branch-or-tag>` to pin; default `main`) |

Notes on `create`:

- `--from` takes a `.yaml` or `.yml` file, not a directory. The deployment
  rejects a file whose `prompt_file` it cannot resolve; install the package
  instead.
- The positional name overrides the name in the YAML.
- Without `--from`, `create` builds a minimal workflow from flags (`--type`,
  `--description`, `--repo`, `--ref`, `--repos`, `--no-repos`); those flags
  conflict with `--from`.

`install --dry-run` (`-n`) shows what would be registered without
registering it.

### 7. Update a workflow in place

Re-register it the same way it was first registered:

- **First registered with `create --from`:** re-run the same `create --from`.
- **First registered with `install` from a directory:** bump `version` in the
  package manifest (`syntropic137-plugin.json`) and re-run
  `syn workflow install <dir>`, or re-run it with `--force` to overwrite the
  same version. A package with no manifest is recorded as version `0.0.0`.
- **First installed from git or a marketplace:**
  `syn workflow update <package-name>` (accepts `--ref`, `--dry-run`,
  `--force`).

The refusals you can hit, and what each one means:

| message contains | meaning | do |
|---|---|---|
| `version X is already installed. Pass --force to reinstall it.` | same version, changed content | bump the version, or `--force` if overwriting is intended |
| `resolves to a different source than the installed copy` | same version, different source digest | confirm the source is the one you meant, then `--force` |
| `is installed with version ..., but this install declares no version. Refusing to overwrite recorded provenance with nothing.` | it was installed with `install`, and you are updating it with `create --from` | use `syn workflow install <dir> --force`. `--force` does not bypass this refusal from `create`, and `version:` is not a valid YAML key |
| the same refusal naming `source digest` | as above, for the source digest | as above |

A byte-identical reinstall is reported as already installed and changes
nothing. Reinstalling an archived workflow restores it.

### 8. Archive or remove

```bash
syn workflow delete <workflow-id> --force          # archive (soft delete)
syn workflow uninstall <package-name>               # remove an installed package and archive its workflows
syn workflow uninstall <package-name> --keep-workflows
```

`delete` refuses without `--force`. Archived workflows stay visible with
`syn workflow list --include-archived`, and reinstalling one restores it.

## Recommended tools and practices (as of 2026-10-03)

The CLI is the primary surface. When an agent needs structured output or the
CLI is unavailable, the same operations are HTTP calls against
`$SYN_API_URL/api/v1`, with the `Authorization` header that matches the
credentials in use:

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/workflows?include_archived=false&page=1&page_size=50"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/workflows/<workflow-id>"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/workflows/<workflow-id>/runs"
curl -sf -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$SYN_API_URL/api/v1/workflows/<workflow-id>/execute" \
  -d '{"task": "Fix the auth timeout", "inputs": {"base_branch": "develop"}, "repos": ["owner/repo"]}'
```

| endpoint | notes |
|---|---|
| `GET /workflows` | query params `workflow_type`, `include_archived`, `page`, `page_size`, `order_by`. There is no free-text search parameter. |
| `GET /workflows/{id}` | the detail `syn workflow show` reads, including `input_declarations` and `phases` |
| `GET /workflows/{id}/runs` | the history `syn workflow status` reads |
| `POST /workflows/{id}/execute` | body `inputs` (string to string), `task`, `repos`. Returns `execution_id`, `workflow_id`, `status` (`started`), `message`. |

The HTTP path skips the CLI's pre-dispatch checks in step 4, so a direct
`POST` will start a run whose task or inputs are discarded without warning.
Run `syn workflow run ... --dry-run` first if you can.

`syn workflow search` and `syn workflow info` search configured marketplaces,
not the deployment; use `syn workflow list` to find what the deployment can
run. Run `syn workflow <subcommand> --help` for the full flag list of the
installed CLI version.
