---
name: workflow-marketplace
description: Use when finding, reviewing, installing, updating or publishing Syntropic137 workflow packages through a marketplace - registering a marketplace repository, searching it by keyword, category or tag, reading a package's details, reviewing a package for security before installing it, installing or upgrading by name, or exporting a deployed workflow and publishing it as a marketplace. Trigger phrases include "syn marketplace add", "browse the marketplace", "search for a workflow", "find a code review workflow", "install from the marketplace", "install a workflow from the marketplace", "is this workflow safe to install", "review this plugin before installing", "publish my workflow", "share a workflow", "export a workflow", "marketplace.json", "syn workflow search", "syn workflow info". Do NOT use for running, validating or registering a workflow you already have locally (use syn-workflow), for writing a workflow's YAML or phase prompts (use authoring-workflows), or for watching a run (use execution-control).
---

# Syntropic137 workflow marketplaces

A marketplace is a git repository with a `marketplace.json` index at its root.
The index lists a set of workflow packages, and each package lives in a
subdirectory of that repository. Once you register a marketplace with the
`syn` CLI, you can search its index and install a package by name. This
works the same way as installing from a path or a git URL.

Marketplaces are client side. They are recorded on the machine that runs
`syn`, not on the deployment, so searching one never touches the deployment.
Only `install` reaches the deployment. It registers workflows, and those
workflows then run with real credentials against real repositories. This
skill exists to make that one step deliberate. **A package is code that will
run with your credentials.** Phase prompts are instructions to an agent
inside a workspace that holds a repository token. Review them the way you
would review a script before piping it to a shell.

## When to Use

- You want to register, list, refresh or remove a marketplace.
- You are searching for a workflow by keyword, category or tag, or reading
  one package's details.
- You need to decide whether a package is safe to install.
- You are installing, updating or uninstalling a package by name.
- You want to export deployed workflows and publish them as a marketplace.

## When NOT to Use

- The workflow is already on your machine and you want to run, validate or
  register it: use syn-workflow.
- You are writing a workflow's YAML or its phase prompts: use
  authoring-workflows.
- You want to watch a run: use execution-control.

## Input

- **Deployment** (required for install, update and uninstall, set in the
  environment): `SYN_API_URL`, default `http://localhost:8137`. Credentials
  are `SYN_API_TOKEN` (bearer) or `SYN_API_USER` + `SYN_API_PASSWORD`
  (basic). Search and info read only your local marketplace registry and the
  indexes it points at. If `syn` is not installed, run
  `npx @syntropic137/setup cli`.
- **`git`** (tool, required): fetching a marketplace or a package clones it with
  `git`, so `git` must be on the path and able to reach GitHub.
- **Marketplace repository** (`org/repo`, required to register a
  marketplace) and a **ref** (tag or branch, optional) to pin.
- **Package name** (string, required to install by name, review, update or uninstall), which
  you get from `syn workflow search` or `syn workflow info`.
- **Workflow id** (string, required to publish): the deployed workflow to
  export.

## Workflow

1. Before you install, check which deployment you are writing to:

   ```bash
   syn config show     # SYN_API_URL, and whether credentials are set
   syn health          # is that deployment reachable and healthy
   ```

2. Register a marketplace. **Pin what you do not own.** A marketplace or
   package installed from `main` installs whatever `main` is at that moment.

   ```bash
   syn marketplace add org/repo                      # index from main
   syn marketplace add org/repo --ref v1.2.0         # pin a tag or branch (-r)
   syn marketplace add org/repo --name team-flows    # local name (-n); default is the index's name
   syn marketplace list                              # registered marketplaces: name, repo, ref, when added
   syn marketplace refresh                           # re-fetch every index
   syn marketplace refresh team-flows                # re-fetch one
   syn marketplace remove team-flows
   ```

   `add` clones `https://github.com/org/repo.git`. It refuses the repository
   if there is no `marketplace.json` at the root. It also refuses a name that
   is already registered; remove that one first. Fetched indexes are cached
   for four hours, and `refresh` bypasses the cache.

3. Search, then read the package:

   ```bash
   syn workflow search                         # every package in every marketplace
   syn workflow search review                  # matches name, description, category and tags
   syn workflow search -c ci                   # by category (--category)
   syn workflow search -t security             # by tag (--tag), NOT a task
   syn workflow search review -r team-flows    # one marketplace (--registry)
   syn workflow info <package-name>            # version, description, category, tags, source, marketplace
   ```

   `info` shows the first marketplace that lists the name. If two
   marketplaces publish the same name, use `search -r` to pick the one you
   mean, and install from its source directly. **Silence is not absence.**
   Search skips a marketplace whose index cannot be fetched, and prints no
   message. If a search returns nothing, run `syn marketplace list`;
   `syn marketplace refresh <name>` will show the error.

4. Review before installing. Do not install a package just to inspect it.
   Instead, clone the source that `info` printed, at the ref you plan to
   install:

   ```bash
   tmp=$(mktemp -d)
   git clone --depth=1 --branch <ref> https://github.com/org/repo.git "$tmp/repo"
   pkg="$tmp/repo/plugins/pr-review"    # the path in parentheses from `info`
   syn workflow validate "$pkg"         # resolves prompt_file locally, then validates each workflow
   ```

   The package is the entry's `source` path inside the repository, not the
   repository root. Read every phase prompt against the checklist in
   [references/security-review.md](references/security-review.md). It covers
   shell injection, credential and data exfiltration, encoded payloads,
   prompt injection, declared vs instructed tools, reach, external code and
   cost. Report the findings and a verdict: **safe to install**,
   **review recommended** or **do not install**. Then `rm -rf "$tmp"`.

5. Preview, then install:

   ```bash
   syn workflow install <package-name> --dry-run          # resolve and preview only (-n)
   syn workflow install <package-name> --ref v1.2.0
   syn workflow install org/repo --ref v1.2.0             # straight from git, no marketplace
   ```

   **The preview is local.** `install --dry-run` resolves the package on
   your machine and prints what it found. It does not ask the deployment
   whether the workflows are valid.

   A bare name is looked up in your marketplaces first. If no marketplace
   lists it, the name is treated as a source.

   The ref is chosen in this order:
   1. an explicit `--ref` other than `main`;
   2. the ref the marketplace entry pins;
   3. the marketplace's own ref.

   Before anything is written, install checks that the `claude_plugins` and
   `skills` the package needs can be resolved. Each install is recorded
   locally, so `syn workflow packages` lists it with its version and source.

6. Update or remove:

   ```bash
   syn workflow update <package-name> --dry-run
   syn workflow update <package-name>                    # re-fetch from its recorded source
   syn workflow update <package-name> --ref v1.3.0
   syn workflow uninstall <package-name>                 # archive its workflows and forget the install
   syn workflow uninstall <package-name> --keep-workflows
   ```

   If an update drops a workflow from the package, that workflow is archived
   on the deployment. Review the new version as in step 4 before you update.

7. Publish. Export the deployed workflow with
   `syn workflow export <workflow-id>`, which writes `./<slug>-export/`. Then
   put the result in a repository that has a `marketplace.json` at its root.
   The index format, the export flags and the versioning rules are in
   [references/publishing.md](references/publishing.md). Then check the
   repository from the outside, as in Outcome 3.

## Output

- **Search or info:** the package name, version, source (repository and
  path) and marketplace.
- **Review:** the source and ref, the workflows and phases you reviewed, a
  findings table (severity, file, detail), a declared vs instructed table per
  phase, and the verdict.
- **Install or update:** the preview, then the deployment named and the
  workflows registered, with the ref that was used.
- **Publish:** the repository and tag, and a clean
  `install <name> --dry-run` run from a fresh `marketplace add`.

## Outcomes we are looking for

### Outcome 1: nothing is installed unread

- *Signal:* before a package from someone else's repository was installed,
  its phase prompts were read and the review was reported.
- *Signal:* the install that ran is the one that was previewed. When the
  source is not your own, it ran at a pinned ref.

### Outcome 2: a search that finds nothing means there is nothing

- *Signal:* after an empty search, `syn marketplace list` was run, and
  `syn marketplace refresh` too if a marketplace was expected, before
  concluding that the package does not exist.

### Outcome 3: a published package installs for someone else

- *Signal:* starting from a fresh `syn marketplace add` of the published
  repository, `syn workflow search` and
  `syn workflow install <name> --dry-run` find and resolve the package.

## Anti-patterns

- **Installing straight from a search hit.** First read `syn workflow info`,
  then review the source, then preview, and only then install.
- **Trusting the tool list over the prompt.** A narrow `allowed_tools` is a
  real restriction. But any phase that keeps `Bash` can read, write and
  reach the network through the shell. The prompt decides what the phase
  does.
- **Retrying a failed install without looking.** Install is not
  transactional. Workflows created before the failure stay registered, and
  the error says so. Check `syn workflow list` before you run it again.
- **Expecting `--ref main` to override a pinned package.** If a package entry
  pins its own `ref`, that ref wins over the default ref. To override it,
  pass a different ref explicitly.
- **Publishing a bare `workflows/` directory and calling it a marketplace.**
  Without a `marketplace.json` at the repository root, `syn marketplace add`
  refuses it. A repository without an index can still be installed directly
  with `syn workflow install org/repo`.

## Recommended tools and practices (as of 2026-10-04)

### Outcome: nothing is installed unread

- **A shallow clone at the ref you plan to install, plus
  `syn workflow validate` on the package directory.** Ladders up by
  reviewing and validating exactly what will be installed, without
  registering anything. Tradeoffs: validate the package directory, not a
  lone `workflow.yaml` (which cannot resolve its `prompt_file` references)
  and not the marketplace root.
- **The checklist in
  [references/security-review.md](references/security-review.md).** Ladders
  up by covering what a quick read misses: encoded payloads, external
  `claude_plugins` and `skills`, and `sandbox: full-access` (the default when
  it is omitted) on codex phases.
- **`install --dry-run`, then `install --ref <tag>`.** Ladders up by making
  the install that runs the same one you previewed. Tradeoffs: the preview
  is local and does not validate against the deployment.

### Outcome: a search that finds nothing means there is nothing

- **`syn marketplace list` and `syn marketplace refresh <name>`.** Ladders up
  because they surface an index that search skipped silently. Tradeoffs:
  `refresh` re-clones, bypassing the four-hour cache.

### Outcome: a published package installs for someone else

- **`syn workflow export`, with a `marketplace.json` that lists each package
  by `source` path.** Ladders up by producing the layout that
  `marketplace add` accepts. Tradeoffs: bump the manifest `version` on every
  content change, or installers get a refusal instead of an update.

Two workflow API routes are useful directly: validate and export. They are
in [references/http-api.md](references/http-api.md). Run
`syn marketplace --help` and `syn workflow <subcommand> --help` for the full
flag list of the installed CLI version.

## References

- [references/security-review.md](references/security-review.md): package
  layouts, the review checklist, validation and the report shape. Read
  during step 4.
- [references/publishing.md](references/publishing.md): export flags and the
  `marketplace.json` format and rules. Read during step 7.
- [references/http-api.md](references/http-api.md): the validate and export
  routes. Read when you need structured output.

## Continual improvement

File drift, gaps, or proposed updates at
https://github.com/syntropic137/syntropic137-skills/issues
