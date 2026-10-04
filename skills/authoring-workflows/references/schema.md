# Workflow definition schema

Every key the workflow YAML accepts, at the workflow, input, phase and agent
levels, plus prompt-file resolution and the placeholders a prompt can use.
Read this while writing a definition. The deployment's
`syn workflow validate` is the authority; this file describes what it
enforces, and any key not listed here is rejected.

## Workflow level

| key | required | notes |
|---|---|---|
| `id` | yes | 1 to 100 characters. The platform id: registering a definition with an existing id updates that workflow |
| `name` | yes | |
| `description` | no | |
| `type` | no | `research`, `planning`, `implementation`, `review`, `deployment` or `custom` (default). Any other value is stored as `custom` without an error |
| `classification` | no | `simple`, `standard` (default), `complex` or `epic` |
| `requires_repos` | no | Default true. See [traps.md](traps.md), Trap 1 |
| `repository` | no | a default repository: `url` (required), `ref` (default `main`) |
| `repos` | no | a list of default repository URLs |
| `project_name` | no | |
| `inputs` | no | see "Inputs" below |
| `phases` | yes | at least one; ids unique, orders unique |
| `claude_plugins`, `skills` | no | applied to every phase; see "Prompt files, plugins and skills" below |

## Inputs

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
a prompt as `{{name}}`. `repos` and `repository` are reserved and rejected as
input names.

## Phase level

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
| `allowed_tools` | a phase field, not an agent field. See [traps.md](traps.md), Trap 3 |
| `model` | wins over `agent.model` |
| `agent` | see "Agent block" below |
| `clone_repos` | default true. `false` keeps the repository token and `{{repo_url}}` and skips only the checkout |
| `delivers_repo_changes` | default true |
| `argument_hint` | a hint for the task text this phase expects |
| `claude_plugins`, `skills` | applied to this phase only |

Rejected keys: `max_tokens` (use `timeout_seconds`), and any key not listed.
`can_open_pr` is accepted and dropped with a notice.

## Agent block

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
`sandbox: read-only` is refused at authoring.

## Prompt files, plugins and skills

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

## Placeholders

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
