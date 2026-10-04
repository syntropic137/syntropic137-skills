# syntropic137-skills

Harness-agnostic skills for agents **using** a deployed Syntropic137 instance.

## The rule that defines this repo

A skill here may use the **product surface only**: the HTTP API, the `syn` CLI,
and the session store. It may not cite repository paths, `file:line`, ADR
numbers, or internal module names - a consumer of a deployed system does not
have the repository, and a skill that assumes otherwise fails silently in the
only environment it will ever run in.

The check, applicable by anyone in review: **if a skill cites a `file:line`, it
belongs in the `syntropic137/syntropic137` repository instead.**

## Skills only

No commands, no hooks, no agent definitions. Those are harness-specific by
construction and cannot be made agent-agnostic by relocating them.

## Authoring

When creating or editing a skill, use the `authoring-skills` skill:
https://github.com/AgentParadise/agentic-skills/tree/main/skills/meta/authoring-skills
It is the source of truth for skill shape; do not restate its rules here.
