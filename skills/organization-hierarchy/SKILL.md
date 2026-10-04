---
name: organization-hierarchy
description: Use when organising repositories in a Syntropic137 deployment into organizations and systems, or reading health, cost and activity rolled up by repo or system - creating an organization, grouping repos into a system, registering a repository, assigning or moving a repo between systems, or asking which system is failing or costing the most. Trigger phrases include "create an organization", "syn org", "create a system", "group these repos", "register a repo", "syn repo register", "assign repo to system", "move repo to another system", "unassign repo", "system health", "system cost", "which repo is failing", "cost by repo", "repo activity", "what repos can the GitHub App see". Do NOT use for running workflows (use syn-workflow), for setting up trigger rules on a repo (use github-triggers), for installing or configuring the GitHub App itself, or for the cost and token breakdown of one execution or session (use observing-sessions).
---

# Organising repositories in Syntropic137

A deployment groups repositories in a three level hierarchy:

```
Organization            a team or company
  System                a group of repos that ship together (a service and its libraries)
    Repo                one registered git repository
```

The hierarchy is for reading the deployment: health, cost and activity
rolled up per repo and per system. It does not gate what runs. A workflow
runs against any repository passed with `-R`, registered or not, and a
trigger fires for its repository whether or not that repo has a system.

## When to Use

- You are creating an organization or a system, or registering a repository.
- You are assigning a repo to a system, or moving it between systems.
- You want health, cost or activity rolled up per repo or per system: which
  system is failing, which repo costs the most.
- You want to know which repositories the GitHub App can see.

## When NOT to Use

- You want to run a workflow: use syn-workflow.
- You want trigger rules on a repo: use github-triggers.
- You need to install or configure the GitHub App itself: that is deployment
  setup.
- You want the cost and token breakdown of one execution or session: use
  observing-sessions.

## Input

- **Deployment** (required, environment): `SYN_API_URL`, default
  `http://localhost:8137`. Credentials are `SYN_API_TOKEN` (bearer) or
  `SYN_API_USER` + `SYN_API_PASSWORD` (basic). If `syn` is not installed:
  `npx @syntropic137/setup cli`.
- **Organization, system and repo ids** (strings `org-...`, `system-...`,
  `repo-...`, required by every command after `create`): ids, not names. Each
  is printed at creation; list to find one.
- **Repository** (`owner/repo`, required to register): worth registering when
  the GitHub App can reach it.
- **Organization id** (string, optional for `register` when the deployment
  has exactly one organization).

## Workflow

1. Check the deployment, and which repositories its GitHub App can reach,
   which is the set worth registering:

   ```bash
   syn config show                        # SYN_API_URL, and whether credentials are set
   syn health                             # is that deployment reachable and healthy
   syn github repos                       # every repo across installations
   syn github repos -i <installation-id>  # one installation (--installation)
   ```

2. Create the organization:

   ```bash
   syn org create --name "Acme Corp" --slug acme      # -n, -s
   syn org list
   syn org show <org-id>
   syn org update <org-id> --name "Acme Inc"
   syn org delete <org-id> --force                    # -f
   ```

3. Create systems in it:

   ```bash
   syn system create --name "Payments" --org <org-id> --description "Billing and invoicing"   # -n, -o (required), -d
   syn system list --org <org-id>
   syn system show <system-id>
   syn system update <system-id> --name "Billing"
   syn system delete <system-id> --force
   ```

4. Register repositories. **Registration is explicit**: repositories are not
   registered for you when the GitHub App sees them, and `syn repo register`
   is how a repo enters the hierarchy.

   ```bash
   syn repo register --url acme/billing-api --org <org-id>    # -u, -o
   syn repo list --org <org-id>
   syn repo show <repo-id>
   ```

   `--org` may be omitted when the deployment has exactly one organization;
   it is then used. With several organizations, `register` asks you to pass
   one. With none, the repo is registered as unaffiliated. Registering the
   same repo twice is refused as already registered.

5. Assign repos to systems. **One system per repo**: a repo is in at most one
   system, so moving it is an unassign followed by an assign.

   ```bash
   syn repo assign <repo-id> --system <system-id>    # -s
   syn repo unassign <repo-id>
   syn repo list --system <system-id>
   ```

6. Read the rollups:

   ```bash
   syn system status <system-id>      # healthy, degraded or failing; per repo status, success rate, last run
   syn system cost <system-id>        # total cost and tokens, cost by repo
   syn system activity <system-id>    # recent executions (-n, default 20)
   syn system history <system-id>     # longer execution history (-n, default 50)
   syn system patterns <system-id>    # recurring failures and cost outliers

   syn repo health <repo-id>          # success rate, trend, last run
   syn repo cost <repo-id>
   syn repo activity <repo-id>        # -n, default 20
   syn repo failures <repo-id>        # recent failures with error messages (-n, default 10)
   syn repo sessions <repo-id>        # agent sessions for this repo (-n, default 20)
   ```

   **Costs are keyed by repository name.** Repo and system cost come from
   executions whose repository matches the registered `owner/repo` name, so
   they include runs from before the repo was registered or assigned. To
   drill from a rollup into one run, take its execution id to
   execution-control or observing-sessions.

## Output

- The ids created (`org-...`, `system-...`, `repo-...`), and
  `syn repo list --system <system-id>` showing the repos that belong
  together.
- For a rollup question: the figure from `syn system status`,
  `syn system cost` or `syn repo cost`, with the system or repo named.
- For a refusal: its reason and the current state that explains it.

## Outcomes we are looking for

### Outcome 1: every repo you care about is registered and in the right system

- *Signal:* `syn repo list --org <org-id>` shows each repo, and
  `syn repo list --system <system-id>` shows the ones that belong together.
- *Signal:* no repo you care about appears only in an unassigned listing.

### Outcome 2: a rollup question is answered from the rollup

- *Signal:* "which system is failing" is answered from `syn system status`,
  and "where did the money go" from `syn system cost` or `syn repo cost`,
  not by adding up executions by hand.

### Outcome 3: a refused change is understood, not retried

- *Signal:* a "already assigned" or "already registered" refusal leads to
  reading the current state, then a deliberate unassign or no action.

## Anti-patterns

- **Passing `--system` to `syn repo register` and assuming it worked.** The
  flag is accepted but not applied: the repo is registered without a system.
  Assign it afterwards with `syn repo assign`.
- **Retrying an assign that was refused.** Assigning a repo that already has
  a system is refused with "Repo is already assigned to a system". Read where
  it is, then unassign it first if the move is intended.
- **Creating the hierarchy to make triggers or cost tracking work.** Neither
  depends on it. Build it because the rollups are useful to you.
- **Deleting a repo with active triggers.** Deregistering is refused while
  the repo has active trigger rules. Pause or delete those first (see
  github-triggers).

## Recommended tools and practices (as of 2026-10-04)

### Outcome: every repo you care about is registered and in the right system

- **`syn github repos`, then `syn repo register`, then `syn repo assign`.**
  Ladders up by registering from the set the App can actually reach and
  assigning in a separate, checked step. Tradeoffs: `register --system` is
  not applied, so the assign is always a second command.
- **`GET /repos?unassigned=true`.** Ladders up by listing the repos still
  outside any system. Tradeoffs: API only.

### Outcome: a rollup question is answered from the rollup

- **`syn system status`, `syn system cost`, `syn system patterns`.** Ladders
  up by answering "which system" questions in one call. Tradeoffs: cost is
  keyed by repository name and includes runs from before registration.
- **`/insights/overview` and `/insights/cost`** for deployment wide rollups
  across all organizations. Ladders up by answering a question that spans
  every organization from one rollup instead of summing systems by hand.

### Outcome: a refused change is understood, not retried

- **`syn repo show <repo-id>` before a second assign.** Ladders up by showing
  the system a repo is already in. A refusal over the API is HTTP 409 with
  the reason in `detail`.

Every route, its filters, and `DELETE /repos/{id}` (deregistering has no CLI
command) are in [references/http-api.md](references/http-api.md). Run
`syn org --help`, `syn system --help` and `syn repo --help` for the full flag
list of the installed CLI version.

## References

- [references/http-api.md](references/http-api.md): the organization,
  system, repo and insights routes with their filters. Read when you need
  structured output, a filter the CLI lacks, or to deregister a repo.

## Continual improvement

File drift, gaps, or proposed updates at
https://github.com/syntropic137/syntropic137-skills/issues
