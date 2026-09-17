---
name: mining-session-logs
description: Use when turning finished agent runs into written lessons - reviewing session logs or transcripts, auditing where executions fail, finding recurring mistakes or wasted effort, attributing spend to failure classes, or writing a retrospective from a batch of runs. Trigger phrases include "what did we learn from these runs", "review the session logs", "mine the transcripts", "why do executions keep failing", "where is the money going", "write a retrospective", "find repeated mistakes", "audit the last N runs". Do NOT use for debugging one specific failed execution (that is ordinary debugging - read its error and phases directly), for live monitoring of a run in progress, or for deciding whether a single pull request is correct.
---

# Mining session logs into lessons

A finished run is evidence that nobody reads. Dozens of them are a dataset: the
same setup failure in twelve workspaces, one phase quietly consuming a third of
the budget, a tool that is never used and one that is used for everything.

The work is not hard. What makes it fail is that the findings evaporate - they
get relayed in a message, the message scrolls away, and the same analysis gets
run again next month against the same unchanged behaviour. **The output of this
skill is a written artifact and a set of filed actions, not a summary.**

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

## Principles

1. **Pre-fetch the corpus to local files, then analyse.** Analysis agents
   frequently cannot reach the deployment - private networks, VPN-only hosts,
   sandboxed subagents. Pull the data yourself, write it to files, and hand the
   files over. A fleet that spends its first minutes discovering it has no route
   has told you nothing.

2. **Count before you read.** Transcripts run to megabytes. Reading whole files
   exhausts a context window and produces worse answers than `grep -c` and a
   frequency table. Find the frequent patterns first, then open a narrow window
   around two or three of them for verbatim quotes.

3. **Re-derive any load-bearing number before acting on it.** Analysis agents
   miscount, and a miscount is indistinguishable from a finding. Check the ones
   a decision rests on - not all of them. Expect both outcomes: in one real
   audit an agent reported 55 and 50 occurrences of two shell errors where the
   true count for both was zero, while its tool-frequency table from the same
   corpus reproduced exactly.

4. **Structural facets and transcript reading are different instruments.**
   Metadata over *every* session (phase, duration, message count, model, cost)
   is unbiased and cheap. Reading transcripts requires sampling, and any sample
   chosen by size or cost is biased toward difficulty by construction. State
   which instrument each claim rests on; they are not interchangeable.

5. **Read the tool names from the event stream, not the agent's prose.** An
   agent's account of what it did is a summary written by the thing being
   audited. The recorded operations are the observation.

6. **Rank by cost, not by frequency.** The most frequent failure is often the
   cheapest - it fails early, before any expensive phase runs. The failure worth
   fixing first is usually one that dies *late*, discarding work that already
   succeeded. Attribute spend to failure class before deciding what to fix.

7. **A finding with no home is a finding you will rediscover.** Before finishing,
   every item is an issue with a reproduction, a change to a prompt or skill, or
   a recorded decision not to act. This is the principle that is easiest to skip
   and the one that determines whether the exercise was worth its cost.

## Anti-patterns

- **The relayed summary.** Findings exist as a message and nowhere else. The
  next person asks the same question and pays for the same analysis.

- **A percentage with no denominator.** "Most sessions hit setup problems" -
  out of how many, and chosen how?

- **The longest-sessions sample presented as representative.** Sampling the
  biggest transcripts is a reasonable way to find floundering and a terrible way
  to estimate a rate. The bias is fine; leaving it unstated is not.

- **Agent prose treated as observation.** A conclusion sourced to "the agent
  said it ran the tests" rather than to a recorded tool call.

- **Fixing the most frequent thing.** Twelve identical failures costing nothing
  each, fixed first, while one late-stage failure quietly discards finished work
  every time it happens.

- **A retrospective with no actions.** Everything is described, nothing is filed,
  and the behaviour is unchanged next month.

## The procedure

1. **Pull the corpus.** Execution records first - they are small and structured.
   Session metadata next. Transcript bodies last and only for a sample. Write
   everything to local files.

2. **Facet the whole population.** Group executions by status, workflow and
   phase. Sum cost by status. This is unbiased and usually contains the headline
   on its own.

3. **Attribute the failures.** For every non-completed execution, classify the
   failure from its stored error, and sum the spend per class. Quote one error
   verbatim per class - the exact string is what makes a class recognisable next
   time.

4. **Sample transcripts deliberately.** Say why you chose the sample. Longest
   for floundering, failed-only for failure shapes, random for rates.

5. **Fan out the analysis.** One agent per question - failure patterns, cost
   concentration, tool usage, delivery integrity. Give each the local file paths,
   an explicit warning that files are large, and a demand for exact counts with
   distinct-session denominators.

6. **Verify what matters.** Re-derive the numbers you are about to act on.

7. **Write the retrospective.** Window, sample size and method at the top, so a
   later reader can judge the claims without re-running anything. Findings
   ranked by cost. A section for what you could not determine.

8. **File the actions.** Each finding becomes an issue with a reproduction, a
   change, or a recorded non-decision.

## Recommended tools and practices (as of 2026-09-17)

The endpoints below are the deployed product surface. If one has moved, only
this section needs editing.

### Execution records, from the Syntropic137 API

```
GET /api/v1/executions?page_size=100
    -> executions[]: workflow_execution_id, workflow_id, status, total_cost_usd,
       total_tokens, duration_seconds, tool_call_count, completed_phases,
       total_phases, error_message, started_at

GET /api/v1/executions/{id}
    -> phases[]: name, status, model, cost_usd, duration_seconds,
       error_message, artifact_id, operations[]
```

`phases[].operations` is the recorded tool use - the observation that principle 5
refers to. `GET /api/v1/artifacts/{id}` returns a phase's written output.

### Session transcripts, from the session store

```
GET  /v1/sessions/corpus?limit=&cursor=       metadata for analytics, IDs and facets
GET  /v1/sessions/search?tags=&limit=&cursor= keyset search; deployment is a TAG
POST /v1/sessions/raw/batch                   {"session_ids": [...]}, max 10 per call
GET  /status                                  per-machine totals and staleness
```

Sessions carry tags of the form `deployment:<name>`, `workflow_id:<id>`,
`phase_id:<id>`, `execution_id:<id>`. Filter the deployment by **tag** -
`origin_environment` is the container, not the deployment, and filtering on it
returns nothing.

### Counting inside large transcripts

```sh
grep -oh '"name":"[A-Za-z_]*"' raw/*.txt | sort | uniq -c | sort -rn
grep -c "<pattern>" raw/*.txt
grep -l "<pattern>" raw/*.txt | wc -l        # distinct sessions, the denominator
```

Prefer an exact literal over a regex with `.*`, which will match across a whole
line and inflate counts. Verify a suspicious zero with a second spelling before
reporting it as absence.
