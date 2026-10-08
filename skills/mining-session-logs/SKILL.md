---
name: mining-session-logs
description: Use when turning finished agent runs into written lessons - reviewing session logs or transcripts across a batch of runs, auditing where executions fail, finding recurring mistakes or wasted effort, attributing spend to failure classes, or writing a retrospective. Trigger phrases include "what did we learn from these runs", "review the session logs", "mine the transcripts", "why do executions keep failing", "where is the money going", "write a retrospective", "find repeated mistakes", "audit the last N runs". Do NOT use for why one specific execution failed (use execution-control), for what one session did or cost (use observing-sessions), for collecting every session of one run (use discovering-run-sessions), for live monitoring of a run in progress (use execution-control), or for deciding whether a single pull request is correct.
metadata:
  version: "1.1.0"
---

# Mining session logs into lessons

A finished run is evidence that nobody reads. Dozens of them are a dataset: the
same setup failure in twelve workspaces, one phase quietly consuming a third of
the budget, a tool that is never used and one that is used for everything.

The work is not hard. What makes it fail is that the findings evaporate: they
get relayed in a message, the message scrolls away, and the same analysis gets
run again next month against the same unchanged behaviour. **The output of this
skill is a written artifact and a set of filed actions, not a summary.**

## When to Use

- You have a batch of finished runs (a time window, a workflow, a deployment)
  and want to know what they teach.
- Executions keep failing and you want the failure classes ranked by what
  they cost.
- You need to know where the spend goes across many runs.
- You are writing a retrospective that someone else will read later.

## When NOT to Use

- One execution failed and you want to know why: use execution-control.
- One session was expensive or did something odd: use observing-sessions.
- You need every session and transcript of one run: use
  discovering-run-sessions, then come back here if the run joins a batch.
- A run is still in progress: use execution-control.

## Input

- **Window** (required): the date range, workflow or deployment the batch
  covers. It is stated at the top of the retrospective.
- **Deployment API** (required): `$SYN_API_URL` and credentials, for execution
  records.
- **Session store** (required for transcripts): its base URL and the
  `deployment:<name>` tag of the deployment under study.
- **Questions** (optional): what the analysis should answer, for example
  failure patterns, cost concentration, tool usage, delivery integrity.
  Without them, the population facets in step 2 set the agenda.
- **Durable destination** (required): where the retrospective is written, and
  the issue tracker the actions are filed in.

## Workflow

1. **Pull the corpus to local files.** Execution records first: they are small
   and structured. Session metadata next. Transcript bodies last and only for
   a sample. Analysis agents frequently cannot reach the deployment (private
   networks, VPN-only hosts, sandboxed subagents), so pull the data yourself
   and hand the files over. Endpoints and fields are in
   [references/data-sources.md](references/data-sources.md).

2. **Facet the whole population.** Group executions by status, workflow and
   phase. Sum cost by status. Metadata over every session is unbiased and
   cheap, and usually contains the headline on its own.

3. **Attribute the failures.** For every non-completed execution, classify the
   failure from its stored error, and sum the spend per class. Quote one error
   verbatim per class: the exact string is what makes a class recognisable
   next time. Rank classes by cost, not frequency, because the most frequent
   failure often fails early and costs little, while one that dies late
   discards work that already succeeded.

4. **Sample transcripts deliberately, and say why.** Longest for floundering,
   failed-only for failure shapes, random for rates. Any sample chosen by size
   or cost is biased toward difficulty by construction, so it can find
   patterns but cannot estimate a rate.

5. **Count before you read.** Transcripts run to megabytes; reading whole files
   exhausts a context window and produces worse answers than `grep -c` and a
   frequency table. Find the frequent patterns first, then open a narrow
   window around two or three of them for verbatim quotes. Recipes are in
   [references/counting.md](references/counting.md). Read tool names from the
   recorded operations, not the agent's prose: an agent's account of what it
   did is a summary written by the thing being audited.

6. **Fan out the analysis.** One agent per question. Give each the local file
   paths, an explicit warning that files are large, and a demand for exact
   counts with distinct-session denominators.

7. **Re-derive the numbers you are about to act on.** Analysis agents
   miscount, and a miscount is indistinguishable from a finding. Check the
   ones a decision rests on, not all of them. Expect both outcomes: in one
   real audit an agent reported 55 and 50 occurrences of two shell errors
   where the true count for both was zero, while its tool-frequency table from
   the same corpus reproduced exactly.

8. **Write the retrospective.** Window, sample size and method at the top, so a
   later reader can judge the claims without re-running anything. Findings
   ranked by cost, each marked measured or inferred, and each naming which
   instrument it rests on (population metadata or sampled transcripts). A
   section for what you could not determine.

9. **File the actions.** Each finding becomes an issue with a reproduction, a
   prompt or skill change, or a recorded decision not to act. A bug that
   verification certified and that surfaced later also becomes an eval case
   pinned to the commit before its fix (see authoring-workflows), so the
   next workflow change is tested against it. A durable practice the batch
   shows (a failure mode, a recovery that worked) goes into the skill that
   owns that concern. This is the step
   that is easiest to skip and the one that decides whether the exercise was
   worth its cost.

## Output

- A retrospective at a durable path, stating the window, the sample size and
  the method, with findings ranked by cost and a section for what could not
  be determined.
- One filed action per finding: an issue with a reproduction, a prompt or
  skill change, or an explicit "accepted, not worth fixing" with a reason.
- The local corpus files the numbers were derived from, so a reader can
  re-derive them.

## Outcomes we are looking for

### Outcome 1: the lesson outlives the runs

- *Signal:* a retrospective exists at a durable path, naming the window and the
  sample size, and can be found by someone who was not in the session.
- *Signal:* a month later, a question about that period is answered by reading
  it rather than by re-running the analysis.

### Outcome 2: every finding lands somewhere that can change

- *Signal:* each finding became an issue with a reproduction, a prompt or skill
  change, or an explicit "accepted, not worth fixing" with a reason.
- *Signal:* no finding exists only as prose in a chat log.

### Outcome 3: the numbers survive scrutiny

- *Signal:* every number a decision rests on was re-derived independently of
  whoever first produced it.
- *Signal:* claims state whether they are measured or inferred, and no reader
  has to guess which.

### Outcome 4: sampling bias is declared, not hidden

- *Signal:* every claim carries its denominator, and any claim resting on a
  non-random sample says so in the same breath.

## Anti-patterns

- **The relayed summary.** Findings exist as a message and nowhere else. The
  next person asks the same question and pays for the same analysis.

- **A percentage with no denominator.** "Most sessions hit setup problems":
  out of how many, and chosen how?

- **The longest-sessions sample presented as representative.** Sampling the
  biggest transcripts is a reasonable way to find floundering and a terrible way
  to estimate a rate. The bias is fine; leaving it unstated is not.

- **Agent prose treated as observation.** A conclusion sourced to "the agent
  said it ran the tests" rather than to a recorded tool call.

- **Fixing the most frequent thing.** Twelve identical failures costing nothing
  each, fixed first, while one late-stage failure quietly discards finished work
  every time it happens.

- **A fleet with no route to the data.** Analysis agents told to fetch the
  corpus themselves spend their first minutes discovering they cannot reach
  the deployment, and report nothing.

- **A retrospective with no actions.** Everything is described, nothing is filed,
  and the behaviour is unchanged next month.

## Recommended tools and practices (as of 2026-10-07)

### Outcome: the lesson outlives the runs

- **Local corpus files, pulled before any analysis.** Ladders up because the
  retrospective can cite the files its numbers came from, and a later reader
  can re-derive them without the deployment. Tradeoffs: transcripts are large;
  pull bodies only for the sample. Endpoints in
  [references/data-sources.md](references/data-sources.md).
- **Window, sample size and method at the top of the retrospective.** Ladders
  up by letting a reader judge the claims without re-running the analysis.

### Outcome: every finding lands somewhere that can change

- **The project's issue tracker, one issue per finding, with the verbatim
  error string as the reproduction.** Ladders up because an issue has an
  owner and a state, and a chat message has neither. Tradeoffs: filing takes
  time the analysis does not; skipping it is the most common way the exercise
  is wasted.
- **Spend attributed per failure class, from `total_cost_usd` and
  `phases[].cost_usd`.** Ladders up by ranking findings by what fixing them is
  worth, so the first issue filed is the expensive one.
- **`syn eval create --repo owner/repo@<commit-before-fix>` for each escaped
  bug.** Ladders up because a bug the workflow is known to miss becomes a
  case every later workflow change is run against. Tradeoffs: the expected
  finding must be written as the eval's goal, by hand. Details in
  authoring-workflows.

### Outcome: the numbers survive scrutiny

- **`grep -c`, `grep -l | wc -l` and a tool-name frequency table over the
  local files.** Ladders up because exact counts with distinct-session
  denominators can be re-run by anyone. Tradeoffs: a regex with `.*` inflates
  counts; prefer exact literals, and verify a suspicious zero with a second
  spelling. Recipes in [references/counting.md](references/counting.md).
- **`phases[].operations` from `GET /api/v1/executions/{id}` as the record of
  tool use.** Ladders up because it is the observation, not the agent's
  account of itself.

### Outcome: sampling bias is declared, not hidden

- **`GET /v1/sessions/corpus` for metadata over every session, before any
  sampling.** Ladders up because population facets are unbiased, so the
  sampled claims can be compared against them. Tradeoffs: metadata says what
  happened, not why.
- **Filter the deployment by its `deployment:<name>` tag, not
  `origin_environment`.** Ladders up because `origin_environment` is the
  container, and filtering on it returns nothing, which reads as an empty
  population rather than a wrong query.

## References

- [references/data-sources.md](references/data-sources.md): the execution
  and session-store endpoints, their fields, and the session tags. Read at
  step 1.
- [references/counting.md](references/counting.md): shell recipes for exact
  counts and denominators over transcript files. Read at step 5, and hand it
  to every analysis agent.

## Continual improvement

File drift, gaps, or proposed updates at
https://github.com/syntropic137/syntropic137-skills/issues
