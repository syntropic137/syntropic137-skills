# syntropic137-skills

Harness-agnostic skills for agents **using** a deployed Syntropic137 instance.

Install with the [`skills`](https://www.npmjs.com/package/skills) CLI, which is how
Syntropic137 itself installs them into a workspace:

```sh
skills add syntropic137/syntropic137-skills/<skill-name> --agent <agent-key> -y
```

`--agent` accepts `claude-code`, `codex`, `gemini-cli` and ~70 others. The same
skill body serves every one of them.

## What belongs here, and what does not

This repo is for agents operating a **deployed system**. Its skills may use only
the product surface: the HTTP API, the `syn` CLI, and the session store. They may
not reference repository paths, `file:line` citations, ADR numbers, or internal
module names, because a consumer does not have the repository.

That gives the boundary a check anyone can apply in review:

> **If a skill cites a `file:line`, it is in the wrong repo.**

Skills for agents working **on** Syntropic137 - contributing code, debugging the
platform, running experiments against its own workflows - live in the
`syntropic137/syntropic137` repository instead, where internal citations are
exactly what makes them useful.

## Skills only

No slash commands, no hooks, no agent definitions. Those are harness-specific by
construction: Codex has no slash commands, no `SessionStart` hook, and no
subagent definition format. A repo that mixes them cannot honestly claim to be
agent-agnostic, so this one holds a single artifact type.

## Layout

```
skills/<name>/SKILL.md      the skill
skills/<name>/references/   optional depth, loaded only when the body points to it
```

## Contents

| skill | use it when |
|---|---|
| [`mining-session-logs`](skills/mining-session-logs/SKILL.md) | You have a pile of finished agent runs and want to know what they teach - recurring failures, wasted effort, cost concentration - written down so the lesson outlives the runs. |
| [`syn-workflow`](skills/syn-workflow/SKILL.md) | You need to find a workflow, read what inputs it takes, start it with the right task and repositories, or register, update or archive it. |
| [`execution-control`](skills/execution-control/SKILL.md) | A run has started and you need to follow it, cancel it, resume it, or find out why it failed before deciding what to do next. |
