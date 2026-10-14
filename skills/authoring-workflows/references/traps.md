# The three authoring traps

The three mistakes behind most definitions that validate but do not do what
the author meant, or do not validate at all. Read this when a run warns that
something "will be discarded", when a run gets no checkout, when `-t` is refused,
or when an `allowed_tools` key is rejected.

## Trap 1: `requires_repos` and `-R`

`requires_repos` defaults to **true** when omitted. A workflow that works on
a repository needs no setting; the caller passes the repository at run time
with `-R owner/repo`, and phases read it as `{{repo_url}}`.

Set `requires_repos: false` only for work that needs no checkout (research,
summarising a URL). It drops only the workflow's own default repositories
(`repository`, `repos`): a run without `-R` gets none. Repositories passed
with `-R` are still cloned, with no warning. To skip the checkout for one
phase while keeping the repository's token and `{{repo_url}}`, set
`clone_repos: false` on that phase.

Repositories are never inputs. Do not declare an input named `repos` or
`repository`: both names are reserved and the definition is rejected.

## Trap 2: `$ARGUMENTS` is the task, from `-t` or `-i task=`

`$ARGUMENTS` and `{{task}}` both render the task. The caller supplies it with
`-t/--task` (preferred) or `-i task=value`; if both are passed, `-t` wins. A
`default` on a declared input named `task` fills it when neither is passed.
Nothing else does: not another input, not a positional argument.

- A workflow whose prompts never mention `$ARGUMENTS` or `{{task}}` does not
  take a task. `syn workflow run ... -t "..."` is then **refused**, because the
  task would be thrown away.
- A workflow that consumes the task but is run without one (no `-t`, no
  `-i task=`, no `default`) is refused: the CLI errors "Missing required
  inputs" and the API answers 422. A prompt that reads the task makes `task`
  required even when no input declares it. Only a workflow that declares
  `task` with `required: false` dispatches without one; the CLI warns,
  `$ARGUMENTS` renders empty and `{{task}}` is left in the prompt as literal
  text.

If the workflow is meant to take a task, put `$ARGUMENTS` in the first
phase's prompt.

## Trap 3: `allowed_tools` is a PHASE field, not an `agent:` field

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
