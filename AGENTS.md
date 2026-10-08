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

## Keep the skills learning

These skills carry what agents operating Syntropic137 have learned. When an
agent learns a durable practice (a failure mode, a recovery that worked, a
workflow design rule), add it to the skill that owns that concern, not a new
one, and:

- phrase it against the product surface: the `syn` command, API field or
  output line an agent can check;
- state the evidence kind and when it was seen (for example "an execution
  that timed out in its first phase, observed 2026-10-05"), never a
  repository path or issue number;
- verify every command and flag against the current CLI before writing it;
- update that skill's dated Recommended tools section;
- bump that skill's version and add its changelog line (see Versioning).

A practice seen once is an anecdote; write it down when a run outcome shows it.

## Versioning

Each skill has its own semver in its frontmatter, as a quoted string (the
Agent Skills spec allows only string values under `metadata`, and has no
top-level `version` field):

```yaml
metadata:
  version: "1.2.0"
```

Any change to a file under `skills/<name>/` - SKILL.md or a reference - bumps
that skill's version: MAJOR when a trigger the skill used to answer now belongs
to another skill, or a skill is renamed or removed; MINOR for a new practice
or section; PATCH for a correction that changes no advice. Add one line under
`## [Unreleased]` in CHANGELOG.md: `` - `<name>` <version>: <what changed> ``.

`python3 scripts/check_versions.py [base-ref]` fails a change that does not do
both (tests: `python3 -m unittest discover -s scripts`). Run it with
`npx -y skills add . -l`, which must list every skill, before pushing.

**A release is a git tag `vX.Y.Z` on `main`.** To cut one: rename
`[Unreleased]` to `[X.Y.Z] - <date>`, where X.Y.Z is a MAJOR, MINOR or PATCH
bump of the last release by the largest skill bump in it; update the compare
links; merge; then tag the merge commit `vX.Y.Z` and push the tag. Never move
a tag. Do not create per-skill tags such as `<name>@1.2.0`: the `skills` CLI
selects one ref per repository (`owner/repo#ref`), and Syntropic137 rejects a
`@` inside a ref.

Why the tag is the version a consumer gets: the `skills` CLI never reads
`metadata.version`. Its `skills-lock.json` records the source, the `ref` it was
installed from and a hash of the skill folder; `skills update` reinstalls when
the folder's content at that same ref differs, and `experimental_install`
reinstalls from `source#ref`. So a consumer on a branch gets every commit
whatever the version says, and a consumer on a tag gets nothing until they
change the tag. `metadata.version` is what a person, an eval or a run record
reads to say which skill version was used.
