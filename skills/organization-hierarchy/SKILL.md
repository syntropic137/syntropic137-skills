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

## Before you start

```bash
syn config show     # SYN_API_URL, and whether credentials are set
syn health          # is that deployment reachable and healthy
```

`SYN_API_URL` defaults to `http://localhost:8137`. Credentials are
`SYN_API_TOKEN` (bearer) or `SYN_API_USER` + `SYN_API_PASSWORD` (basic). If
`syn` is not installed: `npx @syntropic137/setup cli`.

To see which repositories the deployment's GitHub App can reach, which is the
set worth registering:

```bash
syn github repos                       # every repo across installations
syn github repos -i <installation-id>  # one installation (--installation)
```

## Principles

- **Registration is explicit.** Repositories are not registered for you when
  the GitHub App sees them. `syn repo register` is how a repo enters the
  hierarchy.
- **One system per repo.** A repo is in at most one system. Moving it is an
  unassign followed by an assign.
- **Costs are keyed by repository name.** Repo and system cost come from
  executions whose repository matches the registered `owner/repo` name, so
  they include runs from before the repo was registered or assigned.
- **Ids, not names.** Every command after `create` takes the id printed at
  creation (`org-...`, `system-...`, `repo-...`). List to find one.

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

## The procedure

### 1. Create the organization

```bash
syn org create --name "Acme Corp" --slug acme      # -n, -s
syn org list
syn org show <org-id>
syn org update <org-id> --name "Acme Inc"
syn org delete <org-id> --force                    # -f
```

### 2. Create systems in it

```bash
syn system create --name "Payments" --org <org-id> --description "Billing and invoicing"   # -n, -o (required), -d
syn system list --org <org-id>
syn system show <system-id>
syn system update <system-id> --name "Billing"
syn system delete <system-id> --force
```

### 3. Register repositories

```bash
syn repo register --url acme/billing-api --org <org-id>    # -u, -o
syn repo list --org <org-id>
syn repo show <repo-id>
```

`--org` may be omitted when the deployment has exactly one organization; it
is then used. With several organizations, `register` asks you to pass one.
With none, the repo is registered as unaffiliated. Registering the same repo
twice is refused as already registered.

### 4. Assign repos to systems

```bash
syn repo assign <repo-id> --system <system-id>    # -s
syn repo unassign <repo-id>
syn repo list --system <system-id>
```

To move a repo: `unassign`, then `assign` to the new system.

### 5. Read the rollups

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

To drill from a rollup into one run, take its execution id to
execution-control or observing-sessions.

## Recommended tools and practices (as of 2026-10-03)

The CLI is the primary surface. Every command is an HTTP call against
`$SYN_API_URL/api/v1`:

```bash
AUTH="Authorization: Bearer $SYN_API_TOKEN"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/organizations"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/systems?organization_id=<org-id>"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/repos?unassigned=true"
curl -sf -H "$AUTH" -H "Content-Type: application/json" \
  -X POST "$SYN_API_URL/api/v1/repos/<repo-id>/assign" -d '{"system_id": "<system-id>"}'
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/systems/<system-id>/status"
curl -sf -H "$AUTH" "$SYN_API_URL/api/v1/insights/overview"
```

| endpoint | notes |
|---|---|
| `/organizations`, `/organizations/{id}` | create, list, show, update, delete |
| `/systems`, `/systems/{id}` | list filter `organization_id`; plus `/status`, `/cost`, `/activity`, `/patterns`, `/history` |
| `/repos`, `/repos/{id}` | list filters `organization_id`, `system_id`, `provider`, `unassigned`; plus `/assign` (body `system_id`), `/unassign`, `/health`, `/cost`, `/activity`, `/failures`, `/sessions` |
| `DELETE /repos/{id}` | deregisters a repo; no CLI command. Refused (409) while it has active triggers |
| `/insights/overview`, `/insights/cost`, `/insights/contribution-heatmap` | deployment wide rollups across all organizations |

A refusal comes back as HTTP 409 with the reason in `detail`. Run
`syn org --help`, `syn system --help` and `syn repo --help` for the full flag
list of the installed CLI version.
