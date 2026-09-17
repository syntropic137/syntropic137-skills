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

Follow the `authoring-skills` chassis: the description carries the routing
(explicit trigger phrases, synonyms, and non-triggers), the body opens with what
the skill is rather than when to use it, and durable outcomes precede any
dated tool guidance so that tool churn cannot rot the whole file.

Pin depth in `references/` rather than growing the body past ~500 lines.
