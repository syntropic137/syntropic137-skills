# A complete workflow definition

One worked definition that uses most of the schema: a declared task and an
optional input, a claude phase with restricted tools, and a codex phase that
reads the first phase's output. Read this when you want a starting shape to
copy, or to see how the keys in [schema.md](schema.md) fit together.

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

What each choice shows:

- The task reaches the first prompt as `$ARGUMENTS` and the repository as
  `{{repo_url}}`, so the template carries no hardcoded task or repo.
- `focus` is declared with a `default` and referenced as `{{focus}}`, so a
  value passed with `-i focus=...` is not discarded.
- `allowed_tools` sits on the claude phase, not inside its `agent` block.
- The codex phase sets `sandbox: workspace-write` and no `allowed_tools`,
  because a non-empty list is rejected on codex.
- `{{investigate}}` pulls the first phase's output, cut to 2000 characters,
  which is why the first prompt asks for a five line summary.
