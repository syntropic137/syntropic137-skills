---
name: syntropic137-docs
description: Use when an agent is stuck on, unsure about, or guessing at how Syntropic137 works and needs the official documentation - how to install or self-host it, what a concept means (workflow, phase, execution, session, trigger, workspace, harness, eval), which `syn` command or flag does something, what an API endpoint takes or returns, how to configure secrets, tunnels or the GitHub App, or where a feature is documented. Trigger phrases include "how do I use Syntropic137", "how does syn work", "Syntropic137 docs", "syn docs", "read the docs", "check the documentation", "what does this syn command do", "is there an API for", "what is a phase", "how do I set up", "self-host Syntropic137", "docs for agents", "llms.txt", "I'm stuck", "not sure how this works", "where is this documented". Do NOT use when a more specific skill already covers the task, such as running or registering a workflow (syn-workflow), writing workflow YAML (authoring-workflows), a run already in flight (execution-control), session cost or tool breakdowns (observing-sessions), triggers (github-triggers), or marketplaces (workflow-marketplace). Reach for this one when those do not answer the question.
metadata:
  version: "1.0.0"
---

# Syntropic137 docs for agents

The Syntropic137 documentation is published for agents as plain Markdown: one
index, one file per page, and one file with everything. A guessed `syn` flag or
API field fails at best and does the wrong thing at worst, while the page that
answers it is one fetch away.

## When to Use

- You are unsure how something in Syntropic137 works, or about to guess.
- You need a `syn` command, flag, API endpoint or config key you have not
  seen confirmed this session.
- A sibling skill does not cover the question, or points at a concept it does
  not explain.
- A user asks how to give their own agent the Syntropic137 docs.

## When NOT to Use

- Running, registering or archiving a workflow: use syn-workflow.
- Writing workflow YAML, phases or prompts: use authoring-workflows.
- A run already in flight: use execution-control.
- Cost, token or tool breakdowns of a session: use observing-sessions.
- Triggers: use github-triggers. Marketplaces: use workflow-marketplace.

Those skills carry practices the docs do not. Come back here when they leave
a question open.

## Input

- **Question** (string, required): what you need to know, in your own words.
- **Docs base** (URL, optional): `https://docs.syntropic137.com`. No
  credentials needed.
- **Installed CLI** (optional): `syn` on `PATH`, to confirm a documented
  command against the version the user runs.

## Workflow

1. **Fetch the index:** `https://docs.syntropic137.com/llms.md` (also served
   as `/llms.txt`). It lists every page with a one-line description, so you
   can choose pages without reading them.
2. **Pick one or two pages** whose titles or descriptions match the question.
   The table below gives starting points for common questions.
3. **Fetch each page as Markdown** by adding `.md` to its path:
   `/docs/guide/getting-started` becomes `/docs/guide/getting-started.md`.
   The HTML page carries site chrome that costs context and adds nothing.
4. **Fetch everything only for broad questions** ("explain the platform",
   building a mental model before a large task):
   `https://docs.syntropic137.com/llms-full.md`, several hundred KB.
5. **Confirm against the installed system** before acting. The docs describe
   the latest release and a deployment may be older: `syn <command> --help`
   shows what the installed CLI accepts.
6. **Hand off** once you know what to do. If the task is now running a
   workflow, following a run, reading a session or setting a trigger, the
   matching sibling skill has the practices for it.

| Question | Start at |
|---|---|
| Install, first run, prerequisites | `/docs/guide/getting-started.md` |
| What a term means | `/docs/guide/core-concepts.md`, `/docs/guide/concepts-for-agents.md` |
| A `syn` command or flag | `/docs/cli.md`, then `/docs/cli/<command>.md` |
| An HTTP endpoint | `/docs/api.md`, then `/docs/api/<group>.md` |
| Self-hosting, configuration, secrets, tunnels | `/docs/guide/self-hosting.md`, `/docs/guide/configuration.md` |

Pages move; the index is regenerated with every docs release. If a path here
returns 404, take the current one from the index.

## Output

- An answer grounded in the pages you fetched, with a link to each page used
  (the HTML URL, without `.md`, so a person can open it).
- When the answer came from the docs but not from the installed CLI, say so:
  the user's version may differ.
- For a user who wants their own agent to have the docs: point them at
  `https://docs.syntropic137.com/llms`, which has a system prompt to paste.

## Outcomes we are looking for

- **Answers come from the docs, not from memory.** *Signal:* every command,
  flag or field in your answer appears in a page fetched this session.
- **Reads stay small.** *Signal:* the index plus a few pages, unless the
  question genuinely spans the platform.
- **The user can check the source.** *Signal:* the reply links the pages used.

## Anti-patterns

- **A "how do I" answered from training data.** Syntropic137 changes faster
  than model training; a command seen in older material may be renamed or
  gone, and the answer reads just as confident either way.
- **`llms-full.md` fetched for a one-flag question.** A large share of context
  goes to pages that do not bear on the task, crowding out the work itself.
- **The HTML page read instead of the `.md`.** Same content, more tokens,
  harder to quote.
- **A documented flag used without checking the installed CLI.** On an older
  deployment it fails with an unknown-option error, or worse, is ignored.

## Recommended tools and practices (as of 2026-10-16)

### Answers come from the docs

- **Your harness's web fetch tool, or `curl -s <url>`**, for the `.md` URLs.
  Plain text needs no rendering.
- **`syn <command> --help`** to confirm a documented flag exists in the
  installed version.

### Reads stay small

- **`llms.md` first, every time.** Its one-line descriptions let you choose
  pages without loading them.

## Continual improvement

File drift, gaps, or proposed updates at
https://github.com/syntropic137/syntropic137-skills/issues
