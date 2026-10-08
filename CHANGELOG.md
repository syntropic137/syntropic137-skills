# Changelog

All notable changes to these skills are recorded here. The format follows
[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/). Each skill
carries its own [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
version in `metadata.version`; a release of the repository is the git tag
`vX.Y.Z` of the matching section below. See "Versioning" in AGENTS.md.

Every skill change is one line, `` - `<skill>` <version>: <what changed> ``,
under the section of the kind of change it is. `scripts/check_versions.py`
checks for that line.

## [Unreleased]

## [1.1.0] - 2026-10-07

### Added

- Versioning: `metadata.version` in every SKILL.md, this changelog, release
  tags `vX.Y.Z`, and `scripts/check_versions.py`, which fails a change to a
  skill folder that does not bump the skill's version and add its line here.

### Changed

- `authoring-workflows` 1.1.0: workflow design for quality (new reference
  `designing-for-quality.md`): the escaped-bug eval loop, variants and evals
  per job type and codebase, clean controls, eval environments,
  cross-family verification, and a verifier tool list with Bash is not
  read-only.
- `execution-control` 1.1.0: cancel, queue and outcome practices; a queued
  cancel is confirmed only by status cancelled; resume rather than a
  verify-only workflow when the implementation phase completed; `show`
  prints the failed phase's classification and error.
- `mining-session-logs` 1.1.0: a bug that verification certified and that
  surfaced later becomes an eval case, and a durable practice goes into the
  skill that owns it.
- `syn-workflow` 1.1.0: task-writing practices observed 2026-10-04..07 (new
  reference `writing-tasks.md`), including rewriting the task after a
  first-phase timeout is traced to its scope.

## [1.0.0] - 2026-10-04

First set of skills, recorded retroactively: the content at this date
carried no version field.

### Added

- `authoring-workflows` 1.0.0: writing workflow YAML, phases and prompts.
- `discovering-run-sessions` 1.0.0: every session of one run, delegates and
  native transcripts included.
- `execution-control` 1.0.0: following, cancelling, resuming and diagnosing
  an execution.
- `github-triggers` 1.0.0: running workflows from GitHub events.
- `mining-session-logs` 1.0.0: turning finished runs into written lessons.
- `observing-sessions` 1.0.0: what a session did and what it cost.
- `organization-hierarchy` 1.0.0: organizations, systems and repos.
- `syn-workflow` 1.0.0: finding, starting and registering workflows.
- `workflow-marketplace` 1.0.0: finding, installing and publishing workflow
  packages.

[Unreleased]: https://github.com/syntropic137/syntropic137-skills/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/syntropic137/syntropic137-skills/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/syntropic137/syntropic137-skills/releases/tag/v1.0.0
